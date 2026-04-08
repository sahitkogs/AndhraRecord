"""Prompt definitions for the Amaravati caste classifier."""
from prompts.caste_classifier import (
    SYSTEM_PROMPT,
    build_reference_context,
    load_surname_references,
    # Aliases for backward compatibility
    build_ground_truth_context,
    load_ground_truth,
)
