import streamlit as st
from paperscope.main import fetch_and_summarize, query_db
from paperscope.pdf_parser import extract_text_from_pdf
from paperscope.summarizer import summarize
from paperscope.vector_store import build_index, search_similar

st.set_page_config(page_title="PaperScope", layout="wide")
st.title("📚 PaperScope – Your AI Research Assistant")

option = st.sidebar.radio("Choose an action", [
    "🔍 Search arXiv Papers",
    "🧠 Query Stored Summaries",
    "📄 Upload & Summarize PDF",
    "🔎 Semantic Search (FAISS)"
])

if option == "🔍 Search arXiv Papers":
    keyword_input = st.text_input("Enter keywords (e.g., reinforcement learning for robots)")
    if st.button("Fetch & Summarize"):
        if keyword_input:
            with st.spinner("Fetching and summarizing papers..."):
                data = fetch_and_summarize(keyword_input)
                for item in data[-5:]:
                    st.subheader(item['title'])
                    st.write(item['summary'])
        else:
            st.warning("Please enter some keywords to search.")

elif option == "🧠 Query Stored Summaries":
    query_input = st.text_input("Search within existing summaries")
    if st.button("Run Keyword Search"):
        if query_input:
            results = query_db(query_input)
            if results:
                for item in results:
                    st.subheader(item['title'])
                    st.write(item['summary'])
            else:
                st.info("No matching summaries found.")
        else:
            st.warning("Please enter a query.")

elif option == "📄 Upload & Summarize PDF":
    uploaded_file = st.file_uploader("Upload a PDF research paper", type=["pdf"])
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        with st.spinner("Extracting and summarizing..."):
            text = extract_text_from_pdf("temp.pdf")
            summary = summarize(text)
            st.subheader("Generated Summary")
            st.write(summary)

elif option == "🔎 Semantic Search (FAISS)":
    if st.button("Rebuild Index"):
        with st.spinner("Rebuilding vector index..."):
            build_index()
            st.success("Index rebuilt successfully.")

    semantic_query = st.text_input("Enter a semantic query (e.g., 'robot learning from demonstration')")
    if st.button("Search with FAISS"):
        if semantic_query:
            results = search_similar(semantic_query)
            if results:
                for item in results:
                    st.subheader(item['title'])
                    st.write(item['summary'])
            else:
                st.info("No similar summaries found.")
        else:
            st.warning("Please enter a semantic query.")
