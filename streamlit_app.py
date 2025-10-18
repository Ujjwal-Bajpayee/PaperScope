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
            "🔎 Semantic Search (FAISS)",
            "📚 History"
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

# ========== HISTORY SECTION ==========
elif option == "📚 History":
    st.title("📚 Summary History")
    st.markdown("View and manage your previously summarized papers.")
    
    from paperscope.storage import get_history, clear_history, delete_entry
    from datetime import datetime, timedelta
    
    # Load history FIRST
    history = get_history()
    
    # Show statistics if history exists
    if history:
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Total Papers", len(history))
        
        with metric_col2:
            # Count papers added today
            today = datetime.now().date()
            today_count = sum(
                1 for item in history 
                if datetime.fromisoformat(item.get("timestamp", "2000-01-01")).date() == today
            )
            st.metric("Added Today", today_count)
        
        with metric_col3:
            # Count papers from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            week_count = sum(
                1 for item in history 
                if datetime.fromisoformat(item.get("timestamp", "2000-01-01")) > week_ago
            )
            st.metric("Last 7 Days", week_count)
        
        st.markdown("---")
    
    # Add controls in columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_filter = st.text_input("🔍 Filter by title or keyword", placeholder="Type to filter...")
    
    with col2:
        sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title A-Z"])
    
    with col3:
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.session_state.get("confirm_clear", False):
                clear_history()
                st.success("History cleared!")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm")
    
    st.markdown("---")
    
    if not history:
        st.info("📭 No papers in history yet. Start by searching or uploading papers!")
    else:
        # Apply filters
        if search_filter:
            history = [
                item for item in history 
                if search_filter.lower() in item.get("title", "").lower() 
                or search_filter.lower() in item.get("abstract", "").lower()
            ]
        
        # Apply sorting
        if sort_order == "Oldest First":
            history = sorted(history, key=lambda x: x.get("timestamp", ""))
        elif sort_order == "Title A-Z":
            history = sorted(history, key=lambda x: x.get("title", "").lower())
        
        # Display count
        st.caption(f"Showing {len(history)} paper(s)")
        
        # Display history items
        for idx, item in enumerate(history):
            with st.expander(f"📄 {item.get('title', 'Untitled Paper')}", expanded=(idx == 0)):
                # Top row with metadata and action buttons
                top_col1, top_col2, top_col3 = st.columns([4, 1, 1])
                
                with top_col1:
                    # Show timestamp
                    timestamp = item.get("timestamp", "Unknown date")
                    if timestamp != "Unknown date":
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            timestamp = dt.strftime("%B %d, %Y at %I:%M %p")
                        except:
                            pass
                    st.caption(f"📅 Added: {timestamp}")
                    st.caption(f"🆔 ID: `{item.get('id', 'N/A')}`")
                
                with top_col2:
                    # Add download button for summary
                    summary_text = f"Title: {item.get('title', 'N/A')}\n\n"
                    summary_text += f"Abstract:\n{item.get('abstract', 'N/A')}\n\n"
                    summary_text += f"Summary:\n{item.get('summary', 'N/A')}"
                    
                    st.download_button(
                        label="📥",
                        data=summary_text,
                        file_name=f"{item.get('id', 'paper').replace('/', '_')}_summary.txt",
                        mime="text/plain",
                        key=f"download_{idx}",
                        help="Download summary"
                    )
                
                with top_col3:
                    # Add delete button with bin icon
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete this paper", type="secondary"):
                        if delete_entry(item.get('id')):
                            st.success("Paper deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete paper")
                
                st.markdown("---")
                
                # Display abstract
                st.markdown("**Abstract:**")
                st.markdown(f"> {item.get('abstract', 'No abstract available.')}")
                
                # Display summary
                st.markdown("**Summary:**")
                st.info(item.get('summary', 'No summary available.'))
                
                # Add link if it's an arXiv paper
                paper_id = item.get('id', '')
                if 'arxiv' in paper_id.lower() or '/' in paper_id:
                    arxiv_id = paper_id.split('/')[-1] if '/' in paper_id else paper_id
                    st.markdown(f"🔗 [View on arXiv](https://arxiv.org/abs/{arxiv_id})")
