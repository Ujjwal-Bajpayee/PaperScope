import os
import re

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def summarize(text: str) -> str:
    """Simple extractive demo summarizer used only in Demo Mode.

    Returns a structured summary prefixed with a demo notice.
    """
    text = (text or "").strip()
    if not text:
        return "(no text provided)"

    # Extract first sentence for objective
    sentences = re.split(r'(?<=[.!?])\s+', text)
    objective = sentences[0] if sentences else "The paper's main objective."

    summary = f"""[DEMO MODE]
- **Objective**: {objective}
- **Methodology**: A quantitative approach was used.
- **Key Findings**:
    - Finding A was discovered.
- **Contribution**: The paper introduces a new method.
"""
    return summary
