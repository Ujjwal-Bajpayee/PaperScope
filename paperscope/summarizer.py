import google.generativeai as genai 

from paperscope.config import API_KEY, MODEL

genai.configure(api_key=API_KEY)

def summarize(text):
    """
    Generate a summary of the provided text using Gemini API.
    """
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(f"Summarize this research abstract:\n\n{text}")
    return response.text.strip()
