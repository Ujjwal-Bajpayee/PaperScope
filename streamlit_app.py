import os
import streamlit as st
from paperscope.main import fetch_and_summarize, query_db
from paperscope.pdf_parser import extract_text_from_pdf
from paperscope.vector_store import build_index, search_similar

# Set Streamlit page config
st.set_page_config(page_title="PaperScope", page_icon="📄", layout="wide")

# Check for demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
if DEMO_MODE:
    from paperscope.summarizer_demo import summarize
else:
    from paperscope.summarizer import summarize

# ===== 🎨 Custom Styling =====
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
    </style>
""", unsafe_allow_html=True)

# ===== 📚 Sidebar Navigation =====
with st.sidebar:
    st.markdown('<div class="sidebar-title">📂 Navigation</div>', unsafe_allow_html=True)

    option = st.radio(
        label="Choose a section",                          # ✔ Accessibility-safe label
        options=[
            "🔍 Search arXiv Papers",
            "🧠 Query Stored Summaries",
            "📄 Upload & Summarize PDF",
            "🔎 Semantic Search (FAISS)"
        ],
        key="main_menu",
        label_visibility="collapsed"                      # ✔ Hides the label visually
    )

    if DEMO_MODE:
        st.markdown("---")
        st.markdown("🟠 **Demo Mode Active**")
        st.caption("Results are approximate.")

        if st.button("🎯 Load Demo Dataset"):
            from paperscope.demo_data import load_demo_data
            ok, msg = load_demo_data(build_index=False)
            st.success(msg) if ok else st.error(msg)

# ===== 🧠 Main Header & Description =====
st.markdown('<div class="main-title">📚 PaperScope – Your AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Your personal assistant for academic research using LLMs</div>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===== 🔍 Search arXiv Papers =====
if option == "🔍 Search arXiv Papers":
    keyword_input = st.text_input("Enter Keywords", placeholder="e.g., reinforcement learning for robots")

    if st.button("🔎 Fetch & Summarize"):
        if DEMO_MODE:
            st.info("This feature is disabled in Demo Mode. Use demo dataset or upload a PDF instead.")
        elif keyword_input:
            with st.spinner("Fetching and summarizing..."):
                data = fetch_and_summarize(keyword_input)
                if data:
                    for item in data[-5:]:
                        with st.expander(f"📄 {item['title']}"):
                            st.write(item['summary'])
                else:
                    st.warning("No results found.")
        else:
            st.warning("Please enter a keyword to search.")

# ===== 🧠 Query Stored Summaries =====
elif option == "🧠 Query Stored Summaries":
    query_input = st.text_input("Search stored summaries", placeholder="e.g., contrastive learning")

    if st.button("🔍 Run Keyword Search"):
        if query_input:
            results = query_db(query_input)
            if results:
                for item in results:
                    with st.expander(f"📄 {item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No matching summaries found.")
        else:
            st.warning("Please enter a query.")

# ===== 📄 Upload & Summarize PDF =====
elif option == "📄 Upload & Summarize PDF":
    uploaded_file = st.file_uploader("📤 Upload a PDF research paper", type=["pdf"])

    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        with st.spinner("🧠 Extracting and summarizing..."):
            text = extract_text_from_pdf("temp.pdf")
            summary = summarize(text)

            st.subheader("📝 Generated Summary")
            st.success(summary)

# ===== 🔎 Semantic Search (FAISS) =====
elif option == "🔎 Semantic Search (FAISS)":
    if st.button("🔄 Rebuild Index"):
        if DEMO_MODE:
            st.info("Index building is simulated in Demo Mode. Load the demo instead.")
        else:
            with st.spinner("Rebuilding semantic vector index..."):
                build_index()
                st.success("Index rebuilt successfully.")

    semantic_query = st.text_input("Enter a semantic query", placeholder="e.g., visual prompt tuning in robotics")

    if st.button("🔍 Search with FAISS"):
        if semantic_query:
            results = search_similar(semantic_query)
            if results:
                for item in results:
                    with st.expander(f"📄 {item['title']}"):
                        st.write(item['summary'])
            else:
                st.info("No similar summaries found.")
        else:
            st.warning("Please enter a semantic query.")
