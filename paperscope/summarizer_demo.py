import os
import re

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


def summarize(text: str) -> str:
    """Simple extractive demo summarizer used only in Demo Mode.

    Returns a fixed, structured demo summary.
    """
    return """
[DEMO MODE]

**Objective:** To demonstrate the new structured summary format.
**Methodology:** This demo skips AI generation and returns a hard-coded string.
**Key Findings:** * The new format is much easier to read.
* Markdown is rendered correctly.
**Contribution:** This feature improves the app's usability as per issue #18.
    """
