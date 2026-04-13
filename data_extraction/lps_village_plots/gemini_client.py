"""Gemini API client for caste classification."""
import json
import os
import time


try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


from caste_classifier import SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT

CASTE_NORMALIZE = {
    # Case normalization only — no merging
    'kamma': 'Kamma', 'kapu': 'Kapu', 'reddy': 'Reddy',
    'brahmin': 'Brahmin', 'vysya': 'Vysya', 'muslim': 'Muslim',
    'sc': 'SC', 'st': 'ST', 'velama': 'Velama',
    'kshatriya': 'Kshatriya', 'yadava': 'Yadava',
    'christian': 'Christian', 'other': 'Other', 'unknown': 'Unknown',
    'mala': 'Mala', 'madiga': 'Madiga',
    'scheduled caste': 'Scheduled Caste', 'scheduled tribe': 'Scheduled Tribe',
    'lambada': 'Lambada', 'bagata': 'Bagata', 'jatapu': 'Jatapu',
    'konda dora': 'Konda Dora', 'koya': 'Koya',
    'padmasali': 'Padmasali', 'mudiraj': 'Mudiraj', 'gouda': 'Gouda',
    'settibalija': 'Settibalija', 'balija': 'Balija',
    'surya balija': 'Surya Balija', 'vadabalija': 'Vadabalija',
    'gavara': 'Gavara', 'jalari': 'Jalari', 'kalinga': 'Kalinga',
    'kurni': 'Kurni', 'kuruba': 'Kuruba', 'boya': 'Boya',
    'agnikula kshatriya': 'Agnikula Kshatriya',
    'k velama': 'K Velama', 'p velama': 'P Velama',
    't kapu': 'T Kapu',
    'telaga': 'Telaga',
}


class GeminiClient:
    """Wrapper for Gemini API calls for caste classification."""

    def __init__(self, api_key=None, model=None, system_prompt=None):
        if genai is None:
            raise ImportError("google-genai package required. Install: pip install google-genai")

        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Set GEMINI_API_KEY environment variable or pass api_key")

        self.client = genai.Client(api_key=self.api_key)
        self.model = model or os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def classify_batch(self, name_village_pairs, ground_truth_context=None):
        """Classify a batch of (name, village) pairs.

        Args:
            name_village_pairs: list of (full_name, village) tuples
            ground_truth_context: optional string with ground truth info for the surnames

        Returns:
            list of dicts with name, name_type, caste, confidence, reasoning
        """
        names_text = "\n".join(
            f"- {name} (village: {village})" for name, village in name_village_pairs
        )

        prompt = "Classify these Amaravati land beneficiaries:\n\n" + names_text
        if ground_truth_context:
            prompt += f"\n\nGround truth context for these surnames:\n{ground_truth_context}"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.1,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=int(os.environ.get('GEMINI_THINKING_BUDGET', '1024'))
                    ),
                ),
            )
            result = json.loads(response.text)
            if isinstance(result, dict):
                for v in result.values():
                    if isinstance(v, list):
                        return v
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"  Gemini error: {e}", flush=True)
            return []

    def classify_single(self, full_name, village="", ground_truth_context=None):
        """Classify a single name. Returns dict."""
        results = self.classify_batch([(full_name, village)], ground_truth_context)
        return results[0] if results else {'name': full_name, 'caste': 'Unknown', 'confidence': 'low'}

    @staticmethod
    def normalize_caste(caste_raw):
        """Normalize caste value to standard category."""
        if not caste_raw or str(caste_raw).lower() in ('null', 'none', ''):
            return 'Unknown'
        return CASTE_NORMALIZE.get(str(caste_raw).lower().strip(), str(caste_raw).strip())
