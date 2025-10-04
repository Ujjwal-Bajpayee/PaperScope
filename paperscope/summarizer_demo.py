import os
import re

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def summarize(text: str) -> str:
    """Simple extractive demo summarizer used only in Demo Mode.

    Returns the first 1-2 sentences prefixed with a demo notice.
    """
    text = (text or "").strip()
    if not text:
        return "(no text provided)"
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) >= 2:
        summary = " ".join(sentences[:2]).strip()
    else:
        summary = text[:300].strip()
    return f"[DEMO MODE] {summary}"
