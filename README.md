# 📚 PaperScope – Your AI-Powered Research Assistant

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub stars](https://img.shields.io/github/stars/Ujjwal-Bajpayee/PaperScope.svg?style=social&label=Star)](https://github.com/Ujjwal-Bajpayee/PaperScope)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2025-orange.svg)](https://hacktoberfest.com/)
[![GitHub issues](https://img.shields.io/github/issues/Ujjwal-Bajpayee/PaperScope.svg)](https://github.com/Ujjwal-Bajpayee/PaperScope/issues)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Ujjwal-Bajpayee/PaperScope/actions)

**PaperScope** is an intelligent research assistant that helps you discover, summarize, and search academic papers efficiently.  
Built with **Gemini**, **FAISS**, and **Streamlit**, it transforms how you interact with research — making exploration faster, smarter, and more insightful. 🧠✨

---

## 🚀 Overview

PaperScope empowers researchers, students, and enthusiasts to:
- 🔍 **Search** papers from **arXiv** instantly by topic or keyword.  
- 🧾 **Summarize** academic papers using **Gemini AI**.  
- 📄 **Upload PDFs** and generate concise summaries.  
- 🔎 **Perform semantic search** using **FAISS** to find contextually similar papers.  

---

## 🧩 Features

### 🔍 Search arXiv Papers
Easily search for recent papers and get concise, AI-generated summaries powered by Gemini.

### 🧠 Query Stored Summaries
Retrieve relevant summaries from your saved data using keyword or semantic search.

### 📄 Upload & Summarize PDFs
Upload your own research paper or document — PaperScope summarizes it in seconds.

### 🔎 Semantic Search (FAISS)
Find papers with similar meanings, not just matching keywords, using FAISS-based vector search.

---

## 🛠️ Tech Stack

| Component | Purpose |
|------------|----------|
| **Streamlit** | Interactive user interface |
| **arXiv API** | Academic paper data source |
| **Google Gemini** | AI model for summaries & insights |
| **FAISS** | Vector-based semantic search |
| **PyMuPDF** | PDF parsing and text extraction |

---

## ✅ Quick start — run locally

These steps will get PaperScope running locally on macOS (zsh) or Linux. The project expects a small configuration file (`paperscope/config.py`) to provide your Gemini API key, the model name to use, and a path for the local JSON DB.

1. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a minimal configuration file at `paperscope/config.py`.
   This repository does not include credentials. Create the file with these three variables:

```python
# paperscope/config.py
API_KEY = "YOUR_GOOGLE_GENAI_API_KEY"  # keep this secret
MODEL = "your-gemini-model-name"      # e.g. a text/generative model identifier
DB_PATH = "db.json"                   # path for the local JSON database
```

4. Start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

5. Open the URL printed by Streamlit (usually http://localhost:8501) in your browser and use the sidebar to choose actions: Search arXiv, Query Stored Summaries, Upload & Summarize PDF, or Semantic Search (FAISS).

## ⚙️ What the app creates / uses

- `db.json` (or the file you set in `DB_PATH`) — local JSON database of fetched summaries.
- `faiss.index` and `meta.json` — created by the FAISS index builder when you run the "Rebuild Index" action.
- `temp.pdf` — a temporary file used when you upload a PDF from the Streamlit UI.

## 📝 Notes & troubleshooting

- Missing `paperscope/config.py`: the code imports `API_KEY`, `MODEL`, and `DB_PATH` from `paperscope.config`. If you forget to create this file you will see an ImportError. Create the file as shown above.
- Google Gemini / `google-generativeai`: ensure your API key is active and has access to the model you picked. Keep the key secret — do not commit it to git.
- FAISS install issues on macOS: if `pip install faiss-cpu` fails, try using conda:

```bash
conda install -c conda-forge faiss-cpu
```

- If `fitz` (PyMuPDF) import fails, ensure the `PyMuPDF` package is installed (it is listed in `requirements.txt`).

## 🔒 Security and costs

- Using Google Gemini / other generative APIs may incur costs. Monitor usage in your cloud console and set appropriate limits/alerts.
- Never commit `paperscope/config.py` with real keys to a public repository. This file is already included in the project's `.gitignore`, so you do not need to add it yourself.

## 🧪 Demo Mode

PaperScope supports a lightweight Demo Mode so reviewers and curious users can try the app without providing a Gemini API key.

- Enable Demo Mode by setting the environment variable `DEMO_MODE=1` (or `true`/`yes`) before starting the app. Example:

```bash
DEMO_MODE=1 streamlit run streamlit_app.py
```

- Demo Mode does not call external generative APIs. Instead, the app returns simplified extractive summaries and deterministic embeddings so the core UI and search flows can be explored offline.
- A banner appears in the UI when Demo Mode is active and some features may be simplified or show the `[DEMO MODE]` prefix in results.
- Demo Mode is intended for evaluation and demos only. For production use or higher-quality summaries, unset `DEMO_MODE` and add a valid `paperscope/config.py` with your Gemini credentials.

### Demo checks

A small verification script is provided to assert demo mode works without external APIs:

```bash
DEMO_MODE=1 python3 scripts/demo_mode_check.py
```

This script saves a sample summary, builds the FAISS index (using local embeddings) and runs a semantic search to confirm the flow works offline.

## Community & Code of Conduct

PaperScope is developed in an open and collaborative spirit. Please read and follow the project's Code of Conduct before contributing or participating. The full policy is available in `CODE_OF_CONDUCT.md`.

If you encounter behavior that violates the Code of Conduct, please follow the reporting instructions described in `CODE_OF_CONDUCT.md`.