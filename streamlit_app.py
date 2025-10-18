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
            border-left: 2px solid transparent;
            transition: all 0.15s ease;
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
        
        .stRadio > div > label[data-checked="true"] {
            background-color: rgba(47, 129, 247, 0.1);
            border-left-color: var(--accent-primary);
            color: var(--accent-primary);
            font-weight: 600;
        }
        
        .stRadio > div > label[data-checked="true"]:hover {
            background-color: rgba(47, 129, 247, 0.15);
        }
        
        /* Hide radio button circles */
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
        
        /* Improved scrollbar */
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
    st.markdown('<div class="caption-text">                                                                              </div>', unsafe_allow_html=True)

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