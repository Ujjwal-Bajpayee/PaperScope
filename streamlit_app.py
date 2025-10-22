import os
import io
import re
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import streamlit as st
from fpdf import FPDF

# Import project modules
from paperscope.main import fetch_and_summarize, query_db
from paperscope.pdf_parser import extract_text_from_pdf
from paperscope.vector_store import build_index, search_similar

# Optional: history storage API
try:
    from paperscope.storage import get_history, clear_history, delete_entry, save_history_entry
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    def get_history():
        return []
    def clear_history():
        pass
    def delete_entry(entry_id):
        return False
    def save_history_entry(entry):
        pass

# Check for demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
if DEMO_MODE:
    from paperscope.summarizer_demo import summarize
else:
    from paperscope.summarizer import summarize

# Application configuration
st.set_page_config(page_title="PaperScope", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------

def safe_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem/download use."""
    if not filename:
        return "file"
    filename = filename.split("/")[-1].split("\\")[-1]
    filename = re.sub(r"[^\w\-_.]", "_", filename)
    return filename[:200]


def generate_pdf_from_text(title: str, metadata: dict, body_text: str, annotations: str = ""):
    """Generate a Unicode-safe PDF summary report using fpdf2."""
    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join(os.path.dirname(__file__), "paperscope", "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 16)
    else:
        pdf.set_font("Helvetica", "", 16)

    pdf.cell(0, 10, txt=title[:100], ln=True, align="C")
    pdf.ln(10)

    if os.path.exists(font_path):
        pdf.set_font("DejaVu", "", 12)
    else:
        pdf.set_font("Helvetica", "", 12)
    
    if metadata:
        for key, value in metadata.items():
            pdf.multi_cell(0, 8, f"{key}: {str(value)[:100]}")
        pdf.ln(6)

    pdf.multi_cell(0, 8, body_text)
    pdf.ln(10)

    if annotations:
        if os.path.exists(font_path):
            pdf.set_font("DejaVu", "B", 13)
        else:
            pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Annotations:", ln=True)
        if os.path.exists(font_path):
            pdf.set_font("DejaVu", "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 8, annotations)

    try:
        pdf_bytes = pdf.output(dest="S")
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode("latin-1")
    except Exception:
        pdf_bytes = pdf.output(dest="S").encode("utf-8")

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer


def safe_write_temp_file(uploaded_file, filename="temp.pdf") -> str:
    """Save uploaded file to a safe temporary path and return path."""
    tmp_dir = tempfile.gettempdir()
    path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}_{filename}")
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    return path


def validate_summary(s: Optional[str]) -> bool:
    return bool(s and s.strip())


def parse_iso(iso_str: str) -> datetime:
    """Parse ISO timestamp robustly, returning epoch if fails."""
    if not iso_str:
        return datetime.fromtimestamp(0)
    try:
        return datetime.fromisoformat(iso_str)
    except Exception:
        try:
            return datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.fromtimestamp(0)


def to_date(iso_str: str) -> Optional[datetime.date]:
    try:
        return parse_iso(iso_str).date()
    except Exception:
        return None


# ---------------------------------------------------------------------
# Custom CSS & Styles (Modern Dark Theme)
# ---------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-hover: #30363d;
            --bg-card: #1c2128;
            --border-primary: #30363d;
            --border-secondary: #484f58;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-tertiary: #6e7681;
            --accent-primary: #2f81f7;
            --accent-hover: #1f6feb;
            --accent-active: #388bfd;
            --success: #3fb950;
            --warning: #d29922;
            --error: #f85149;
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.6);
        }
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        .stApp {
            background-color: var(--bg-primary);
        }
        
        .main {
            background-color: var(--bg-primary);
            padding: 2rem 3rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header-container {
            background: transparent;
            padding: 2.5rem 0 2rem 0;
            margin-bottom: 2.5rem;
            position: relative;
        }
        
        .main-title {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.04em;
            line-height: 1.1;
        }
        
        .main-subtitle {
            font-size: 1.125rem;
            color: var(--text-secondary);
            font-weight: 400;
            line-height: 1.6;
            max-width: 650px;
        }
        
        section[data-testid="stSidebar"] {
            background-color: var(--bg-primary);
            border-right: 1px solid var(--border-primary);
        }
        
        section[data-testid="stSidebar"] > div {
            background-color: var(--bg-primary);
            padding: 2rem 1.25rem;
        }
        
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0;
        }
        
        section[data-testid="stSidebar"] .stRadio {
            background-color: transparent;
            padding: 0;
        }
        
        .sidebar-title {
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 1.5rem;
            padding: 0;
        }
        
        .stRadio > div {
            gap: 0;
            background-color: transparent;
            display: flex;
            flex-direction: column;
        }
        
        .stRadio > div > label {
            background-color: transparent;
            padding: 0.875rem 1rem;
            border-radius: 0;
            border: none;
            border-left: 3px solid transparent;
            transition: all 0.2s ease;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--text-secondary);
            position: relative;
            text-align: left;
            margin-bottom: 0.25rem;
        }
        
        .stRadio > div > label:hover {
            background-color: rgba(48, 54, 61, 0.4);
            color: var(--text-primary);
        }
        
        /* Active state using adjacent sibling selector */
        .stRadio > div > label:has(input[type="radio"]:checked) {
            background-color: rgba(47, 129, 247, 0.15);
            border-left-color: #2f81f7;
            color: #2f81f7;
            font-weight: 600;
        }
        
        .stRadio > div > label:has(input[type="radio"]:checked):hover {
            background-color: rgba(47, 129, 247, 0.2);
        }
        
        .stRadio > div > label:has(input[type="radio"]:checked) > div:last-child::before {
            content: "● ";
            color: #2f81f7;
        }
        
        .stRadio > div > label > div:first-child {
            display: none;
        }
        
        .section-wrapper {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
            border: none;
            margin-bottom: 3rem;
            box-shadow: none;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.75rem;
            padding-bottom: 0;
            border-bottom: none;
            letter-spacing: -0.02em;
        }
        
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid var(--border-primary);
            padding: 0.875rem 1.25rem;
            font-size: 0.95rem;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(47, 129, 247, 0.1);
            outline: none;
            background-color: var(--bg-hover);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: var(--text-tertiary);
        }
        
        .stTextInput label {
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .stButton > button {
            background: var(--accent-primary);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 0.875rem 2rem;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
            box-shadow: var(--shadow-sm);
        }
        
        .stButton > button:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(47, 129, 247, 0.3);
        }
        
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: var(--shadow-sm);
        }
        
        .streamlit-expanderHeader {
            background-color: var(--bg-tertiary);
            border-radius: 8px;
            border: 1px solid var(--border-primary);
            font-weight: 500;
            color: var(--text-primary);
            padding: 1.25rem 1.5rem;
            transition: all 0.2s ease;
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }
        
        .streamlit-expanderHeader:hover {
            border-color: var(--border-secondary);
            background-color: var(--bg-hover);
        }
        
        .streamlit-expanderContent {
            border: 1px solid var(--border-primary);
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 1.5rem;
            background-color: var(--bg-tertiary);
            color: var(--text-secondary);
            line-height: 1.8;
            font-size: 0.925rem;
            margin-top: -0.75rem;
            margin-bottom: 0.75rem;
        }
        
        .streamlit-expander {
            margin-bottom: 0.75rem;
        }
        
        [data-testid="stFileUploader"] {
            background-color: var(--bg-tertiary);
            border: 2px dashed var(--border-primary);
            border-radius: 12px;
            padding: 3rem 2rem;
            transition: all 0.2s ease;
            text-align: center;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent-primary);
            background-color: var(--bg-hover);
        }
        
        [data-testid="stFileUploader"] label {
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.95rem;
        }
        
        .stAlert {
            border-radius: 10px;
            border: 1px solid var(--border-primary);
            padding: 1rem 1.25rem;
            background-color: var(--bg-tertiary);
            margin: 1rem 0;
            font-size: 0.9rem;
        }
        
        .caption-text {
            font-size: 0.85rem;
            color: var(--text-tertiary);
            margin-top: 0.5rem;
            line-height: 1.5;
        }
        
        .stMarkdown, p, span, div {
            color: var(--text-primary);
        }
        
        .demo-indicator {
            background: linear-gradient(135deg, var(--warning) 0%, #b87803 100%);
            color: #ffffff;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 700;
            margin: 1rem 0;
            display: inline-block;
            box-shadow: var(--shadow-sm);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stSpinner > div {
            border-color: var(--accent-primary) transparent transparent transparent !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
        }
        
        .stSubheader {
            color: var(--text-primary);
            font-weight: 600;
            font-size: 1.35rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        [data-testid="stCaption"] {
            color: var(--text-tertiary);
            font-size: 0.85rem;
        }
        
        [data-testid="stSpinner"] {
            text-align: center;
        }
        
        hr {
            border: none;
            height: 1px;
            background-color: var(--border-primary);
            margin: 1.5rem 0;
        }
        
        .stSuccess {
            background-color: rgba(63, 185, 80, 0.12);
            border-left: 3px solid var(--success);
            color: var(--text-primary);
        }
        
        .stError {
            background-color: rgba(248, 81, 73, 0.12);
            border-left: 3px solid var(--error);
            color: var(--text-primary);
        }
        
        .stWarning {
            background-color: rgba(210, 153, 34, 0.12);
            border-left: 3px solid var(--warning);
            color: var(--text-primary);
        }
        
        .stInfo {
            background-color: rgba(47, 129, 247, 0.12);
            border-left: 3px solid var(--accent-primary);
            color: var(--text-primary);
        }
        
        .stDownloadButton > button {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
            border-radius: 8px;
            padding: 0.6rem 1.25rem;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        .stDownloadButton > button:hover {
            background: var(--bg-hover);
            border-color: var(--accent-primary);
            color: var(--accent-primary);
            transform: translateY(-1px);
        }
        
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-secondary);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-tertiary);
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Navigation</div>', unsafe_allow_html=True)
    
    option = st.radio(
        label="Choose a section",
        options=[
            "Search arXiv Papers",
            "Query Stored Summaries",
            "Upload & Summarize PDF",
            "Semantic Search (FAISS)",
            "History"
        ],
        key="main_menu",
        label_visibility="collapsed"
    )

    if DEMO_MODE:
        st.markdown('<div class="demo-indicator">Demo Mode</div>', unsafe_allow_html=True)
        st.caption("Results are approximate")
        
        if st.button("Load Demo Dataset"):
            try:
                from paperscope.demo_data import load_demo_data
                ok, msg = load_demo_data(build_index=False)
                if ok:
                    st.success(msg)
                else:
                    st.error("Failed to load demo database")
            except ImportError:
                st.error("Demo data module not found")

# ---------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------
st.markdown("""
    <div class="header-container">
        <div class="main-title">PaperScope</div>
        <div class="main-subtitle">Your personal assistant for academic research using LLMs</div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: Search arXiv Papers
# ---------------------------------------------------------------------
if option == "Search arXiv Papers":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Search arXiv Papers</div>', unsafe_allow_html=True)
    
    keyword_input = st.text_input(
        "Enter Keywords or Paper URL",
        placeholder="e.g., reinforcement learning for robots OR https://arxiv.org/abs/2301.12345"
    )
    st.markdown('<div class="caption-text">You can enter keywords to search arXiv, or paste a direct paper URL (arXiv or PDF link)</div>', unsafe_allow_html=True)

    if st.button("Fetch & Summarize"):
        if DEMO_MODE:
            st.info("This feature is disabled in Demo Mode. Use demo dataset or upload a PDF instead.")
        elif not keyword_input or keyword_input.strip() == "":
            st.warning("Please enter a keyword or URL to search")
        else:
            try:
                from paperscope.url_handler import is_url
                
                if is_url(keyword_input):
                    with st.spinner("Fetching paper from URL and summarizing..."):
                        data = fetch_and_summarize(keyword_input)
                        
                        if data:
                            st.success("Paper fetched and summarized successfully")
                            for idx, item in enumerate(data[-5:]):
                                with st.expander(f"{item.get('title', 'Untitled Paper')}"):
                                    st.markdown("**Summary:**")
                                    st.write(item.get("summary", "No summary available"))
                                    
                                    # Download buttons
                                    summary_text = item.get('summary', '')
                                    md_bytes = f"# {item.get('title', 'Summary')}\n\n{summary_text}".encode("utf-8")
                                    txt_bytes = summary_text.encode("utf-8")
                                    
                                    metadata = {
                                        "source": item.get('source', 'arXiv'),
                                        "paper_id": item.get('id', 'N/A')
                                    }
                                    pdf_buf = generate_pdf_from_text(
                                        title=item.get('title', 'PaperScope Summary'),
                                        metadata=metadata,
                                        body_text=summary_text,
                                        annotations=item.get('annotations', '')
                                    )
                                    
                                    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
                                    with dl_col1:
                                        st.download_button(
                                            label="Download TXT",
                                            data=txt_bytes,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                            mime="text/plain",
                                            key=f"download_txt_arxiv_{idx}"
                                        )
                                    with dl_col2:
                                        st.download_button(
                                            label="Download MD",
                                            data=md_bytes,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                            mime="text/markdown",
                                            key=f"download_md_arxiv_{idx}"
                                        )
                                    with dl_col3:
                                        st.download_button(
                                            label="Download PDF",
                                            data=pdf_buf,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                            mime="application/pdf",
                                            key=f"download_pdf_arxiv_{idx}"
                                        )
                        else:
                            st.error("Failed to fetch paper from URL. Please check the URL and try again")
                            st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
                            
                else:
                    with st.spinner("Fetching and summarizing..."):
                        data = fetch_and_summarize(keyword_input)
                        
                        if data:
                            st.success(f"Found and processed {len(data)} paper(s)")
                            for idx, item in enumerate(data[-10:][::-1]):
                                with st.expander(f"{item.get('title', 'Untitled Paper')}"):
                                    st.markdown("**Summary:**")
                                    st.write(item.get("summary", "No summary available"))
                                    
                                    # Download buttons
                                    summary_text = item.get('summary', '')
                                    md_bytes = f"# {item.get('title', 'Summary')}\n\n{summary_text}".encode("utf-8")
                                    txt_bytes = summary_text.encode("utf-8")
                                    
                                    metadata = {
                                        "source": item.get('source', 'arXiv'),
                                        "paper_id": item.get('id', 'N/A')
                                    }
                                    pdf_buf = generate_pdf_from_text(
                                        title=item.get('title', 'PaperScope Summary'),
                                        metadata=metadata,
                                        body_text=summary_text,
                                        annotations=item.get('annotations', '')
                                    )
                                    
                                    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
                                    with dl_col1:
                                        st.download_button(
                                            label="Download TXT",
                                            data=txt_bytes,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                            mime="text/plain",
                                            key=f"download_txt_arxiv_{idx}"
                                        )
                                    with dl_col2:
                                        st.download_button(
                                            label="Download MD",
                                            data=md_bytes,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                            mime="text/markdown",
                                            key=f"download_md_arxiv_{idx}"
                                        )
                                    with dl_col3:
                                        st.download_button(
                                            label="Download PDF",
                                            data=pdf_buf,
                                            file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                            mime="application/pdf",
                                            key=f"download_pdf_arxiv_{idx}"
                                        )
                        else:
                            st.warning("No results found")
                            
            except Exception as e:
                st.error(f"Error processing: {str(e)}")
                st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: Query Stored Summaries
# ---------------------------------------------------------------------
elif option == "Query Stored Summaries":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Query Stored Summaries</div>', unsafe_allow_html=True)
    
    query_input = st.text_input(
        "Search stored summaries",
        placeholder="e.g., contrastive learning"
    )

    if st.button("Run Keyword Search"):
        if not query_input or query_input.strip() == "":
            st.warning("Please enter a search query")
        else:
            with st.spinner("Searching database..."):
                try:
                    results = query_db(query_input)
                    
                    if not results:
                        st.info("No matching summaries found")
                    else:
                        st.success(f"Found {len(results)} results")
                        for idx, item in enumerate(results):
                            with st.expander(f"{item.get('title', 'Untitled')}", expanded=(idx == 0)):
                                st.markdown("**Summary:**")
                                st.write(item.get('summary', 'No summary available'))

                                # Download buttons
                                download_col1, download_col2, download_col3 = st.columns([1, 1, 1])
                                summary_text = item.get('summary', '')
                                md_bytes = f"# {item.get('title', '')}\n\n{summary_text}".encode("utf-8")
                                txt_bytes = summary_text.encode("utf-8")
                                pdf_buf = generate_pdf_from_text(
                                    title=item.get('title', 'Summary'),
                                    metadata={"id": item.get('id', '')},
                                    body_text=summary_text,
                                    annotations=item.get('annotations', '')
                                )
                                
                                with download_col1:
                                    st.download_button(
                                        label="TXT",
                                        data=txt_bytes,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                        mime="text/plain",
                                        key=f"query_txt_{idx}"
                                    )
                                with download_col2:
                                    st.download_button(
                                        label="MD",
                                        data=md_bytes,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                        mime="text/markdown",
                                        key=f"query_md_{idx}"
                                    )
                                with download_col3:
                                    st.download_button(
                                        label="PDF",
                                        data=pdf_buf,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                        mime="application/pdf",
                                        key=f"query_pdf_{idx}"
                                    )

                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: Upload & Summarize PDF
# ---------------------------------------------------------------------
elif option == "Upload & Summarize PDF":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload & Summarize PDF</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload a PDF research paper", type=["pdf"])

    if uploaded_file:
        try:
            tmp_path = safe_write_temp_file(uploaded_file, filename="uploaded.pdf")
        except Exception as e:
            st.error(f"Error saving uploaded file: {e}")
            st.stop()

        with st.spinner("Extracting text from PDF..."):
            try:
                extracted_text = extract_text_from_pdf(tmp_path)
            except Exception as e:
                st.error(f"Extraction failed: {e}")
                st.info("Make sure PDF contains selectable text (not scanned images) or use OCR-enabled parsing")
                st.stop()

            if not extracted_text or len(extracted_text.strip()) == 0:
                st.error("No text extracted from PDF. The file may be scanned or encrypted")
                st.stop()

        with st.spinner("Generating AI-powered summary..."):
            try:
                summary_text = summarize(extracted_text)
            except Exception as e:
                st.error(f"Summarization failed: {e}")
                st.stop()

        if not validate_summary(summary_text):
            st.error("Generated an empty summary. Try again or adjust summarizer settings")
            st.stop()

        st.subheader("Generated Summary")
        st.success("Summary generated successfully")
        st.write(summary_text)

        # Save to history
        if STORAGE_AVAILABLE:
            try:
                history_entry = {
                    "id": f"local-{uuid.uuid4().hex[:8]}",
                    "title": uploaded_file.name,
                    "abstract": "",
                    "summary": summary_text,
                    "timestamp": datetime.now().isoformat(),
                    "source": "upload",
                    "annotations": ""
                }
                save_history_entry(history_entry)
            except Exception:
                pass

        # Download options
        st.markdown("---")
        st.markdown("### Download Your Summary")

        col_txt, col_md, col_pdf = st.columns(3)
        txt_bytes = summary_text.encode("utf-8")
        md_bytes = f"# {uploaded_file.name}\n\n{summary_text}".encode("utf-8")
        
        metadata = {
            "Original Filename": uploaded_file.name,
            "Generated On": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Source": "Uploaded PDF"
        }
        pdf_buffer = generate_pdf_from_text(
            title=uploaded_file.name,
            metadata=metadata,
            body_text=summary_text,
            annotations=""
        )

        with col_txt:
            st.download_button(
                label="Download TXT",
                data=txt_bytes,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.txt",
                mime="text/plain",
                key="download_upload_txt"
            )
        with col_md:
            st.download_button(
                label="Download MD",
                data=md_bytes,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.md",
                mime="text/markdown",
                key="download_upload_md"
            )
        with col_pdf:
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.pdf",
                mime="application/pdf",
                key="download_upload_pdf"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: Semantic Search (FAISS)
# ---------------------------------------------------------------------
elif option == "Semantic Search (FAISS)":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Semantic Search (FAISS)</div>', unsafe_allow_html=True)
    
    if st.button("Rebuild Index"):
        if DEMO_MODE:
            st.info("Index building is simulated in Demo Mode. Load the demo instead")
        else:
            with st.spinner("Rebuilding semantic vector index..."):
                try:
                    build_index()
                    st.success("Index rebuilt successfully")
                except Exception as e:
                    st.error(f"Failed to rebuild index: {e}")

    semantic_query = st.text_input(
        "Enter a semantic query",
        placeholder="e.g., visual prompt tuning in robotics"
    )

    if st.button("Search with FAISS"):
        if not semantic_query or semantic_query.strip() == "":
            st.warning("Please enter a semantic query")
        else:
            with st.spinner("Running semantic search..."):
                try:
                    results = search_similar(semantic_query)
                    
                    if not results:
                        st.info("No similar results found")
                    else:
                        st.success(f"Found {len(results)} similar items")
                        for idx, item in enumerate(results):
                            with st.expander(f"{item.get('title', 'Untitled')}", expanded=(idx == 0)):
                                st.markdown("**Summary:**")
                                st.write(item.get('summary', 'No summary available'))

                                download_col1, download_col2, download_col3 = st.columns([1, 1, 1])
                                summary_text = item.get('summary', '')
                                md_bytes = f"# {item.get('title', '')}\n\n{summary_text}".encode("utf-8")
                                txt_bytes = summary_text.encode("utf-8")
                                pdf_buf = generate_pdf_from_text(
                                    title=item.get('title', 'Summary'),
                                    metadata={"id": item.get('id', '')},
                                    body_text=summary_text,
                                    annotations=item.get('annotations', '')
                                )
                                
                                with download_col1:
                                    st.download_button(
                                        label="TXT",
                                        data=txt_bytes,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                        mime="text/plain",
                                        key=f"faiss_txt_{idx}"
                                    )
                                with download_col2:
                                    st.download_button(
                                        label="MD",
                                        data=md_bytes,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                        mime="text/markdown",
                                        key=f"faiss_md_{idx}"
                                    )
                                with download_col3:
                                    st.download_button(
                                        label="PDF",
                                        data=pdf_buf,
                                        file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                        mime="application/pdf",
                                        key=f"faiss_pdf_{idx}"
                                    )

                except Exception as e:
                    st.error(f"Semantic search failed: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: History
# ---------------------------------------------------------------------
elif option == "History":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Summary History</div>', unsafe_allow_html=True)
    st.markdown('<div class="caption-text">View, filter, and download previously processed papers</div>', unsafe_allow_html=True)
    
    try:
        history = get_history() or []
    except Exception:
        history = []
    
    if history:
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Papers", len(history))
        with metric_col2:
            today = datetime.now().date()
            today_count = sum(
                1 for item in history
                if to_date(item.get("timestamp")) == today
            )
            st.metric("Added Today", today_count)
        with metric_col3:
            week_ago = datetime.now() - timedelta(days=7)
            week_count = sum(
                1 for item in history
                if parse_iso(item.get("timestamp")) > week_ago
            )
            st.metric("Last 7 Days", week_count)
        st.markdown("---")
    
    col_filter, col_sort, col_action = st.columns([3, 2, 1])
    with col_filter:
        search_filter = st.text_input("Filter by title or keyword", placeholder="Type to filter...")
    with col_sort:
        sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title A-Z"])
    with col_action:
        if st.button("Clear All", type="secondary"):
            if st.session_state.get("confirm_clear", False):
                try:
                    clear_history()
                    st.success("History cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear history: {e}")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm")
    
    st.markdown("---")
    
    if not history:
        st.info("No papers in history yet. Start by searching or uploading papers!")
    else:
        filtered = history
        if search_filter and search_filter.strip():
            q = search_filter.lower()
            filtered = [
                item for item in filtered
                if q in (item.get('title', '').lower() + 
                        item.get('abstract', '').lower() + 
                        item.get('summary', '').lower())
            ]
        
        if sort_order == "Newest First":
            filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)
        elif sort_order == "Oldest First":
            filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''))
        elif sort_order == "Title A-Z":
            filtered = sorted(filtered, key=lambda x: x.get('title', '').lower())
        
        st.caption(f"Showing {len(filtered)} paper(s)")
        
        for idx, item in enumerate(filtered):
            with st.expander(f"{item.get('title', 'Untitled Paper')}", expanded=(idx == 0)):
                top_col1, top_col2, top_col3 = st.columns([4, 1, 1])
                
                with top_col1:
                    timestamp = item.get('timestamp', 'Unknown date')
                    if timestamp and timestamp != "Unknown date":
                        try:
                            ts = datetime.fromisoformat(timestamp)
                            timestamp = ts.strftime("%B %d, %Y at %I:%M %p")
                        except ValueError:
                            pass
                    st.caption(f"Added: {timestamp}")
                    st.caption(f"ID: `{item.get('id', 'N/A')}`")
                
                with top_col2:
                    summary_text = f"Title: {item.get('title', 'N/A')}\n\n"
                    summary_text += f"Abstract:\n{item.get('abstract', 'N/A')}\n\n"
                    summary_text += f"Summary:\n{item.get('summary', 'N/A')}\n\n"
                    txt_bytes = summary_text.encode("utf-8")
                    
                    st.download_button(
                        label="Download",
                        data=txt_bytes,
                        file_name=f"{safe_filename(item.get('id', 'paper'))}_summary.txt",
                        mime="text/plain",
                        key=f"history_download_{idx}",
                        help="Download summary as TXT"
                    )
                
                with top_col3:
                    if st.button("Delete", key=f"delete_{idx}", help="Delete this paper", type="secondary"):
                        try:
                            if delete_entry(item.get('id')):
                                st.success("Paper deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete paper")
                        except Exception as e:
                            st.error(f"Error deleting: {e}")
                
                st.markdown("---")
                st.markdown("**Abstract:**")
                st.markdown(f"> {item.get('abstract', 'No abstract available')}")
                st.markdown("**Summary:**")
                st.write(item.get('summary', 'No summary available'))
                
                paper_id = item.get('id', '')
                if paper_id and ('arxiv' in paper_id.lower() or '/' in paper_id):
                    arxiv_id = paper_id.split('/')[-1] if '/' in paper_id else paper_id
                    st.markdown(f"[View on arXiv](https://arxiv.org/abs/{arxiv_id})")
                
                st.markdown("---")
                st.markdown("**Additional Formats:**")
                dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
                
                md_content = f"# {item.get('title', '')}\n\n**Abstract:**\n\n{item.get('abstract','')}\n\n**Summary:**\n\n{item.get('summary','')}"
                md_bytes = md_content.encode("utf-8")
                
                pdf_buf = generate_pdf_from_text(
                    title=item.get('title', 'History Entry'),
                    metadata={
                        "id": item.get('id', ''),
                        "added_on": item.get('timestamp', '')
                    },
                    body_text=item.get('summary', ''),
                    annotations=item.get('annotations', '')
                )
                
                with dl_col1:
                    st.download_button(
                        label="TXT",
                        data=txt_bytes,
                        file_name=f"{safe_filename(item.get('title', 'paper'))}.txt",
                        mime="text/plain",
                        key=f"history_txt_{idx}"
                    )
                with dl_col2:
                    st.download_button(
                        label="MD",
                        data=md_bytes,
                        file_name=f"{safe_filename(item.get('title', 'paper'))}.md",
                        mime="text/markdown",
                        key=f"history_md_{idx}"
                    )
                with dl_col3:
                    st.download_button(
                        label="PDF",
                        data=pdf_buf,
                        file_name=f"{safe_filename(item.get('title', 'paper'))}.pdf",
                        mime="application/pdf",
                        key=f"history_pdf_{idx}"
                    )
    
    st.markdown('</div>', unsafe_allow_html=True)
