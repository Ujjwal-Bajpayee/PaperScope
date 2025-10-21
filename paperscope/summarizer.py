import google.generativeai as genai 

from paperscope.config import API_KEY, MODEL

genai.configure(api_key=API_KEY)


def summarize(text):
    """
    Generate a summary of the provided text using Gemini API.
    """
    model = genai.GenerativeModel(MODEL)

    # New structured prompt
    prompt = f"""
    Analyze the following research text and provide a structured breakdown. 
    Use this exact Markdown format:

    **Objective:** The main goal or question of the study.
    **Methodology:** The methods, techniques, or approach used by the researchers.
    **Key Findings:** A list of the most important results or conclusions.
    **Contribution:** What is new, unique, or significant about this paper's contribution to the field.

    ---
    Text to analyze:
    {text}
    """

    response = model.generate_content(prompt)
    return response.text.strip()
