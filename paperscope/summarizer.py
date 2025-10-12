import google.generativeai as genai 

from paperscope.config import API_KEY, MODEL

genai.configure(api_key=API_KEY)

def summarize(text):
    """
    Generate a structured, concise summary of the provided text using Gemini API.
    """
    model = genai.GenerativeModel(MODEL)
    prompt = f"""Analyze the following research abstract and provide a structured, concise summary in Markdown format. Keep each section to a maximum of two sentences. The summary should include the following sections:

- **Objective**: The main goal of the study.
- **Methodology**: The methods used by the researchers.
- **Key Findings**: A bulleted list of the most important results.
- **Contribution**: What is new or unique about this paper.

Abstract:
{text}
"""
    response = model.generate_content(prompt)
    return response.text.strip()
