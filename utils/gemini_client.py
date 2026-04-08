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


CASTE_NORMALIZE = {
    'kamma': 'Kamma', 'kapu': 'Kapu', 'reddy': 'Reddy',
    'brahmin': 'Brahmin', 'vysya': 'Vysya', 'muslim': 'Muslim',
    'sc': 'SC', 'st': 'ST', 'velama': 'Velama',
    'kshatriya': 'Kshatriya', 'yadava': 'Yadava',
    'christian': 'Christian', 'other': 'Other', 'unknown': 'Unknown',
    'scheduled caste': 'SC', 'scheduled tribe': 'ST',
    'balija': 'Kapu', 'telaga': 'Kapu', 'mala': 'SC', 'madiga': 'SC',
    'other bc': 'Other', 'other backward class (bc)': 'Other',
    'kapu, kamma': 'Kapu',
}

DEFAULT_SYSTEM_PROMPT = """You are an expert on caste demographics in the Krishna-Guntur region of Andhra Pradesh, India. You classify land beneficiary names from official APCRDA (Amaravati Capital Region) records.

For each person, determine their most likely caste community. Use EVERYTHING in the name — surname, given names, caste suffixes, honorifics, deity references, all of it.

Key knowledge:
- Telugu names: surname comes FIRST ("ALURI VENKATA RAO" = surname ALURI)
- Caste suffixes: Reddy/Reddi = Reddy. Chowdary/Choudary/Chodary = Kamma. Setty/Setti/Shetty = Vysya.
- Naidu can be Kamma or Kapu. Raju can be Kshatriya or just a name. Rayudu = Kapu.
- Deity names: Vasavi = Vysya community deity.
- Christian given names (Israel, John, Mary, David, Glory, Jerusalem, Abraham, Solomon, Paul) = Christian regardless of surname.
- Muslim given names (Mohammad, Noor, Ahmed, Basha, Khadar) = Muslim regardless of surname.
- Some surnames are shared. Pick the MOST COMMON caste for that surname in Krishna-Guntur.
- Non-person entries (businesses, institutions, data artifacts) should be flagged.
- These are agricultural landowners in rural villages near Amaravati.

Be decisive. Do not use "Unknown" unless truly unclassifiable (single initials, gibberish).

For each name return: name, name_type (person/non_person), caste, confidence (high/medium/low), reasoning.
Categories: Kamma, Kapu, Reddy, Brahmin, Vysya, Muslim, SC, ST, Velama, Kshatriya, Yadava, Christian, Other

Return JSON: {"results": [...]}"""


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
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
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
