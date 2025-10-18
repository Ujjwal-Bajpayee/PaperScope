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

# ===== Enhanced Loading Indicator Styles =====
# Added custom CSS for professional loading animations including:
# - Spinning loader, pulsing dots, and progress bar animations
# - Smooth, GPU-accelerated animations for better performance
st.markdown("""
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 10px;
        }
        .main-subtitle {
            font-size: 18px;
            color: #bbbbbb;
            margin-bottom: 20px;
        }
        .section-divider {
            border: none;
            height: 1px;
            background-color: #444;
            margin: 30px 0;
        }
        .stRadio > div {
            flex-direction: column;
        }
        .sidebar-title {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .sidebar-radio label {
            font-size: 16px !important;
            padding: 8px 14px;
            border-radius: 8px;
        }
        .sidebar-radio label:hover {
            background-color: #333 !important;
            color: #fff !important;
        }
        
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .loading-spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left-color: #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-dots {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .loading-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #4CAF50;
            animation: pulse 1.4s ease-in-out infinite;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .loading-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes pulse {
            0%, 80%, 100% {
                opacity: 0.3;
                transform: scale(0.8);
            }
            40% {
                opacity: 1;
                transform: scale(1.2);
            }
        }
        
        .loading-text {
            margin-top: 1rem;
            font-size: 16px;
            color: #aaa;
            text-align: center;
        }
        
        .progress-bar-container {
            width: 100%;
            height: 4px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            animation: progress 2s ease-in-out infinite;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-title">📂 Navigation</div>', unsafe_allow_html=True)

    option = st.radio(
        label="Choose a section",
        options=[
            "🔍 Search arXiv Papers",
            "🧠 Query Stored Summaries",
            "📄 Upload & Summarize PDF",
            "🔎 Semantic Search (FAISS)"
        ],
        key="main_menu",
        label_visibility="collapsed"
    )

    if DEMO_MODE:
        st.markdown("---")
        st.markdown("🟠 **Demo Mode Active**")
        st.caption("Results are approximate.")

        if st.button("🎯 Load Demo Dataset"):
            from paperscope.demo_data import load_demo_data
            ok,msg = load_demo_data(build_index=False)
            _= st.success(msg) if ok else st.error("Failed to load Demo DB")

st.markdown('<div class="main-title">📚 PaperScope — Your AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Your personal assistant for academic research using LLMs</div>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

if option == "🔍 Search arXiv Papers":
    keyword_input = st.text_input("Enter Keywords or Paper URL", placeholder="e.g., reinforcement learning for robots OR https://arxiv.org/abs/2301.12345")
    st.caption("💡 You can enter keywords to search arXiv, or paste a direct paper URL (arXiv or PDF link)")

    if st.button("🔎 Fetch & Summarize"):
        if DEMO_MODE:
            st.info("This feature is disabled in Demo Mode. Use demo dataset or upload a PDF instead.")
        elif keyword_input:
            from paperscope.url_handler import is_url
            
            if is_url(keyword_input):
                # Enhanced: Create placeholder for loading animation with URL-specific message
                loading_placeholder = st.empty()
                
                with loading_placeholder.container():
                    st.markdown("""
                        <div class="loading-container">
                            <div class="loading-spinner"></div>
                            <div class="loading-text">🔍 Fetching paper from URL...</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                try:
                    data = fetch_and_summarize(keyword_input)
                    
                    # Enhanced: Clear loading animation before showing results
                    loading_placeholder.empty()
                    
                    if data:
                        st.success("✅ Paper fetched and summarized successfully!")
                        for item in data[-5:]:
                            with st.expander(f"📄 {item['title']}"):
                                st.write(item['summary'])
                    else:
                        st.error("❌ Failed to fetch paper from URL. Please check the URL and try again.")
                        st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
                except Exception as e:
                    loading_placeholder.empty()
                    st.error(f"❌ Error processing URL: {str(e)}")
                    st.info("Supported formats: arXiv URLs (abs or pdf) and direct PDF links")
            else:
                # Enhanced: Create placeholder for loading animation with keyword search message
                loading_placeholder = st.empty()
                
                with loading_placeholder.container():
                    st.markdown("""
                        <div class="loading-container">
                            <div class="loading-spinner"></div>
                            <div class="loading-text">🔍 Searching arXiv and generating summaries<span class="loading-dots"><span></span><span></span><span></span></span></div>
                            <div class="progress-bar-container">
                                <div class="progress-bar"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                data = fetch_and_summarize(keyword_input)
                
                # Enhanced: Clear loading animation before showing results
                loading_placeholder.empty()
                
                if data:
                    st.success(f"✅ Found and summarized {len(data[-5:])} papers!")
                    for item in data[-5:]:
                        with st.expander(f"📄 {item['title']}"):
                            st.write(item['summary'])
                else:
                    st.warning("No results found.")
        else:
            st.warning("Please enter a keyword or URL to search.")

elif option == "🧠 Query Stored Summaries":
    query_input = st.text_input("Search stored summaries", placeholder="e.g., contrastive learning")

    if st.button("🔍 Run Keyword Search"):
        if query_input:
            # Enhanced: Added loading indicator for database search
            loading_placeholder = st.empty()
            
            with loading_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔍 Searching database<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    </div>
                """, unsafe_allow_html=True)
            
            results = query_db(query_input)
            
            # Enhanced: Clear loading animation before showing results
            loading_placeholder.empty()
            
            if results:
                st.success(f"✅ Found {len(results)} matching summaries!")
                for item in results:
                    with st.expander(f"📄 {item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No matching summaries found.")
        else:
            st.warning("Please enter a query.")

elif option == "📄 Upload & Summarize PDF":
    uploaded_file = st.file_uploader("📤 Upload a PDF research paper", type=["pdf"])

    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        # Enhanced: Two-stage loading animation for PDF extraction and summarization
        loading_placeholder = st.empty()
        
        # Stage 1: PDF extraction
        with loading_placeholder.container():
            st.markdown("""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">📄 Extracting text from PDF<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    <div class="progress-bar-container">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        text = extract_text_from_pdf("temp.pdf")
        
        # Stage 2: Summary generation
        with loading_placeholder.container():
            st.markdown("""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">🧠 Generating AI-powered summary<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    <div class="progress-bar-container">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        summary = summarize(text)
        
        # Enhanced: Clear loading animation before showing summary
        loading_placeholder.empty()

        st.subheader("📝 Generated Summary")
        st.success(summary)

elif option == "🔎 Semantic Search (FAISS)":
    if st.button("🔄 Rebuild Index"):
        if DEMO_MODE:
            st.info("Index building is simulated in Demo Mode. Load the demo instead.")
        else:
            # Enhanced: Added loading indicator for index rebuild
            loading_placeholder = st.empty()
            
            with loading_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔄 Rebuilding semantic vector index<span class="loading-dots"><span></span><span></span><span></span></span></div>
                        <div class="progress-bar-container">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            build_index()
            
            # Enhanced: Clear loading animation before showing success message
            loading_placeholder.empty()
            
            st.success("✅ Index rebuilt successfully!")

    semantic_query = st.text_input("Enter a semantic query", placeholder="e.g., visual prompt tuning in robotics")

    if st.button("🔍 Search with FAISS"):
        if semantic_query:
            # Enhanced: Added loading indicator for semantic search
            loading_placeholder = st.empty()
            
            with loading_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔎 Running semantic similarity search<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    </div>
                """, unsafe_allow_html=True)
            
            results = search_similar(semantic_query)
            
            # Enhanced: Clear loading animation before showing results
            loading_placeholder.empty()
            
            if results:
                st.success(f"✅ Found {len(results)} semantically similar papers!")
                for item in results:
                    with st.expander(f"📄 {item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No similar summaries found.")
        else:
            st.warning("Please enter a semantic query.")