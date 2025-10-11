import os
import streamlit as st
from paperscope.main import fetch_and_summarize, query_db
from paperscope.pdf_parser import extract_text_from_pdf
from paperscope.vector_store import build_index, search_similar

st.set_page_config(page_title="PaperScope", page_icon="📄", layout="wide")

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
if DEMO_MODE:
    from paperscope.summarizer_demo import summarize
else:
    from paperscope.summarizer import summarize

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #1c2128;
            --bg-hover: #21262d;
            --border: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #7d8590;
            --accent: #58a6ff;
            --accent-hover: #1f6feb;
            --success: #3fb950;
            --warning: #d29922;
            --error: #f85149;
        }
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .stApp {
            background-color: var(--bg-primary);
        }
        
        .main {
            background-color: var(--bg-primary);
            padding: 3rem 4rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header-container {
            background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
            padding: 4rem 3rem;
            border-radius: 20px;
            margin-bottom: 3.5rem;
            border: 1px solid var(--border);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .main-title {
            font-size: 3.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 1rem;
            letter-spacing: -0.04em;
            line-height: 1.1;
        }
        
        .main-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            font-weight: 400;
            line-height: 1.7;
            max-width: 600px;
        }
        
        section[data-testid="stSidebar"] {
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border);
        }
        
        section[data-testid="stSidebar"] > div {
            background-color: var(--bg-secondary);
            padding: 2rem 1.5rem;
        }
        
        .sidebar-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 1.5rem;
            padding: 0 0.5rem;
        }
        
        .stRadio > div {
            gap: 0.75rem;
            background-color: transparent;
        }
        
        .stRadio > div > label {
            background-color: var(--bg-tertiary);
            padding: 1.1rem 1.5rem;
            border-radius: 12px;
            border: 1px solid transparent;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            font-weight: 500;
            font-size: 0.95rem;
            color: var(--text-primary);
        }
        
        .stRadio > div > label:hover {
            background-color: var(--bg-hover);
            border-color: var(--accent);
            transform: translateX(6px);
            box-shadow: 0 2px 8px rgba(88, 166, 255, 0.15);
        }
        
        .section-wrapper {
            background-color: var(--bg-secondary);
            padding: 3rem;
            border-radius: 16px;
            border: 1px solid var(--border);
            margin-bottom: 2.5rem;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 2.5rem;
            padding-bottom: 1.25rem;
            border-bottom: 2px solid var(--border);
            letter-spacing: -0.02em;
        }
        
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 1rem 1.5rem;
            font-size: 1rem;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px rgba(88, 166, 255, 0.12);
            outline: none;
            background-color: var(--bg-hover);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: var(--text-secondary);
            opacity: 0.5;
        }
        
        .stTextInput label {
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 1rem 3rem;
            font-weight: 600;
            font-size: 1.05rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
            box-shadow: 0 4px 12px rgba(88, 166, 255, 0.25);
        }
        
        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(88, 166, 255, 0.35);
        }
        
        .stButton > button:active {
            transform: translateY(-1px);
        }
        
        .streamlit-expanderHeader {
            background-color: var(--bg-tertiary);
            border-radius: 12px;
            border: 1px solid var(--border);
            font-weight: 500;
            color: var(--text-primary);
            padding: 1.25rem 1.5rem;
            transition: all 0.3s ease;
            font-size: 1rem;
        }
        
        .streamlit-expanderHeader:hover {
            border-color: var(--accent);
            background-color: var(--bg-hover);
            box-shadow: 0 2px 8px rgba(88, 166, 255, 0.1);
        }
        
        .streamlit-expanderContent {
            border: 1px solid var(--border);
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 1.5rem;
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            line-height: 1.7;
        }
        
        [data-testid="stFileUploader"] {
            background-color: var(--bg-tertiary);
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 4rem 2rem;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--accent);
            background-color: var(--bg-hover);
            box-shadow: 0 4px 16px rgba(88, 166, 255, 0.1);
        }
        
        [data-testid="stFileUploader"] label {
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .stAlert {
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 1.25rem 1.5rem;
            background-color: var(--bg-tertiary);
            margin: 1rem 0;
        }
        
        .caption-text {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.75rem;
            line-height: 1.6;
        }
        
        .stMarkdown, p, span, div {
            color: var(--text-primary);
        }
        
        .demo-indicator {
            background: linear-gradient(135deg, var(--warning) 0%, #c27803 100%);
            color: #ffffff;
            padding: 0.75rem 1.25rem;
            border-radius: 10px;
            font-size: 0.85rem;
            font-weight: 700;
            margin: 1.5rem 0;
            display: inline-block;
            box-shadow: 0 2px 8px rgba(210, 153, 34, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stSpinner > div {
            border-color: var(--accent) transparent transparent transparent !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
        }
        
        .stSubheader {
            color: var(--text-primary);
            font-weight: 600;
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        [data-testid="stCaption"] {
            color: var(--text-secondary);
        }
        
        [data-testid="stSpinner"] {
            text-align: center;
        }
        
        hr {
            border: none;
            height: 1px;
            background-color: var(--border);
            margin: 2rem 0;
        }
        
        .stSuccess {
            background-color: rgba(63, 185, 80, 0.1);
            border-left: 4px solid var(--success);
        }
        
        .stError {
            background-color: rgba(248, 81, 73, 0.1);
            border-left: 4px solid var(--error);
        }
        
        .stWarning {
            background-color: rgba(210, 153, 34, 0.1);
            border-left: 4px solid var(--warning);
        }
        
        .stInfo {
            background-color: rgba(88, 166, 255, 0.1);
            border-left: 4px solid var(--accent);
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-title">Navigation</div>', unsafe_allow_html=True)

    option = st.radio(
        label="Choose a section",
        options=[
            "Search arXiv Papers",
            "Query Stored Summaries",
            "Upload & Summarize PDF",
            "Semantic Search (FAISS)"
        ],
        key="main_menu",
        label_visibility="collapsed"
    )

    if DEMO_MODE:
        st.markdown('<div class="demo-indicator">Demo Mode</div>', unsafe_allow_html=True)
        st.caption("Results are approximate")

        if st.button("Load Demo Dataset"):
            from paperscope.demo_data import load_demo_data
            ok, msg = load_demo_data(build_index=False)
            _ = st.success(msg) if ok else st.error("Failed to load demo database")

st.markdown("""
    <div class="header-container">
        <div class="main-title">PaperScope</div>
        <div class="main-subtitle">Your personal assistant for academic research using LLMs</div>
    </div>
""", unsafe_allow_html=True)

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
        elif keyword_input:
            from paperscope.url_handler import is_url
            
            if is_url(keyword_input):
                with st.spinner("Fetching paper from URL and summarizing..."):
                    try:
                        data = fetch_and_summarize(keyword_input)
                        if data:
                            for item in data[-5:]:
                                with st.expander(f"{item['title']}"):
                                    st.write(item['summary'])
                            st.success("Paper fetched and summarized successfully")
                        else:
                            st.error("Failed to fetch paper from URL. Please check the URL and try again.")
                            st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
                    except Exception as e:
                        st.error(f"Error processing URL: {str(e)}")
                        st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
            else:
                with st.spinner("Fetching and summarizing..."):
                    data = fetch_and_summarize(keyword_input)
                    if data:
                        for item in data[-5:]:
                            with st.expander(f"{item['title']}"):
                                st.write(item['summary'])
                    else:
                        st.warning("No results found")
        else:
            st.warning("Please enter a keyword or URL to search")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif option == "Query Stored Summaries":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Query Stored Summaries</div>', unsafe_allow_html=True)
    
    query_input = st.text_input(
        "Search stored summaries",
        placeholder="e.g., contrastive learning"
    )

    if st.button("Run Keyword Search"):
        if query_input:
            results = query_db(query_input)
            if results:
                for item in results:
                    with st.expander(f"{item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No matching summaries found")
        else:
            st.warning("Please enter a query")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif option == "Upload & Summarize PDF":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload & Summarize PDF</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload a PDF research paper", type=["pdf"])

    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        with st.spinner("Extracting and summarizing..."):
            text = extract_text_from_pdf("temp.pdf")
            summary = summarize(text)

            st.subheader("Generated Summary")
            st.success(summary)
    
    st.markdown('</div>', unsafe_allow_html=True)

elif option == "Semantic Search (FAISS)":
    st.markdown('<div class="section-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Semantic Search (FAISS)</div>', unsafe_allow_html=True)
    
    if st.button("Rebuild Index"):
        if DEMO_MODE:
            st.info("Index building is simulated in Demo Mode. Load the demo instead.")
        else:
            with st.spinner("Rebuilding semantic vector index..."):
                build_index()
                st.success("Index rebuilt successfully")

    semantic_query = st.text_input(
        "Enter a semantic query",
        placeholder="e.g., visual prompt tuning in robotics"
    )

    if st.button("Search with FAISS"):
        if semantic_query:
            results = search_similar(semantic_query)
            if results:
                for item in results:
                    with st.expander(f"{item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No similar summaries found")
        else:
            st.warning("Please enter a semantic query")
    
    st.markdown('</div>', unsafe_allow_html=True)