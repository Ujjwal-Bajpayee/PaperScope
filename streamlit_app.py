import os
import io
import re
import json
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import streamlit as st
from fpdf import FPDF

# Import project modules (must exist in your repository)
from paperscope.main import fetch_and_summarize, query_db
from paperscope.pdf_parser import extract_text_from_pdf
from paperscope.vector_store import build_index, search_similar

# Optional: history storage API from your repo
from paperscope.storage import get_history, clear_history, delete_entry, save_history_entry

# Summarizer selection based on demo flag
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
    """
    Sanitize a filename for safe filesystem/download use.
    Replaces spaces and special characters with underscores.
    """
    # Remove path separators
    filename = filename.split("/")[-1].split("\\")[-1]
    # Replace non-alphanumeric characters with underscore
    filename = re.sub(r"[^\w\-_.]", "_", filename)
    return filename



def generate_pdf_from_text(title: str, metadata: dict, body_text: str, annotations: str = ""):
    """
    Generate a Unicode-safe PDF summary report using fpdf2.
    Supports Indian Rupee symbol (₹), bullets, and other UTF-8 text.
    """
    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join(os.path.dirname(__file__), "paperscope", "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", "", 16)


    # Title
    pdf.cell(0, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    # Metadata section
    pdf.set_font("DejaVu" if os.path.exists(font_path) else "Helvetica", "", 12)
    if metadata:
        for key, value in metadata.items():
            pdf.multi_cell(0, 8, f"{key}: {value}")
        pdf.ln(6)

    # Summary Body
    pdf.set_font("DejaVu" if os.path.exists(font_path) else "Helvetica", "", 12)
    pdf.multi_cell(0, 8, body_text)
    pdf.ln(10)

    # Optional annotations
    if annotations:
        pdf.set_font("DejaVu" if os.path.exists(font_path) else "Helvetica", "B", 13)
        pdf.cell(0, 10, "Annotations:", ln=True)
        pdf.set_font("DejaVu" if os.path.exists(font_path) else "Helvetica", "", 12)
        pdf.multi_cell(0, 8, annotations)

    # ✅ Output directly as bytes (no latin-1 encoding)
    pdf_bytes = pdf.output(dest="S").encode("utf-8")

    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer


def chunk_text_for_pdf(text: str, max_chars: int = 1000) -> List[str]:
    """Split text into chunks for PDF multi_cell to avoid very long lines."""
    if not text:
        return []
    lines = []
    start = 0
    length = len(text)
    while start < length:
        chunk = text[start:start + max_chars]
        # Try to break at newline or sentence boundary for nicer PDF lines
        last_nl = chunk.rfind('\n')
        if last_nl > int(max_chars * 0.25):
            chunk = chunk[:last_nl]
        else:
            # try a sentence end
            last_sent = max(chunk.rfind('. '), chunk.rfind('? '), chunk.rfind('! '))
            if last_sent > int(max_chars * 0.5):
                chunk = chunk[:last_sent + 1]
        lines.append(chunk.strip())
        start += len(chunk)
    return lines


def safe_write_temp_file(uploaded_file, filename="temp.pdf") -> str:
    """
    Save uploaded file to a safe temporary path and return path.
    Returns the path to the saved file.
    """
    tmp_dir = tempfile.gettempdir()
    path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}_{filename}")
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    return path


def prepare_download_bytes(summary_text: str) -> dict:
    """Return different download-ready objects for summary: txt, md, pdf buffer."""
    txt_bytes = summary_text.encode("utf-8")
    md_bytes = f"# Summary\n\n{summary_text}".encode("utf-8")
    pdf_buf = generate_pdf_from_text(title="PaperScope Summary", metadata={}, body_text=summary_text)
    return {"txt": txt_bytes, "md": md_bytes, "pdf": pdf_buf}


def validate_summary(s: Optional[str]) -> bool:
    return bool(s and s.strip())


# ---------------------------------------------------------------------
# Custom CSS & Styles (loading animation + layout)
# ---------------------------------------------------------------------
st.markdown("""
    <style>
        .main-title { font-size: 42px; font-weight: 800; margin-bottom: 10px; color: #e6eef2; }
        .main-subtitle { font-size: 18px; color: #c7d2d9; margin-bottom: 20px; }
        .section-divider { border: none; height: 1px; background-color: #444; margin: 30px 0; }
        .sidebar-title { font-size: 22px; font-weight: bold; margin-bottom: 20px; }
        .loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; margin: 1rem 0; }
        .loading-spinner { border: 4px solid rgba(255, 255, 255, 0.1); border-left-color: #4CAF50; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }
        .loading-dots { display: inline-flex; align-items: center; gap: 8px; margin-left:6px; }
        .loading-dots span { width: 8px; height: 8px; border-radius: 50%; background-color: #4CAF50; animation: pulse 1.4s ease-in-out infinite; }
        .loading-dots span:nth-child(2){ animation-delay: 0.2s; }
        .loading-dots span:nth-child(3){ animation-delay: 0.4s; }
        @keyframes pulse { 0%,80%,100% { opacity: 0.3; transform: scale(0.8);} 40% { opacity: 1; transform: scale(1.2);} }
        .loading-text { margin-top: 0.6rem; font-size: 14px; color: #aaa; }
        .progress-bar-container { width: 100%; height: 6px; background-color: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; margin-top: 10px; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); animation: progress 2s ease-in-out infinite; }
        @keyframes progress { 0% { width: 0%; } 50% { width: 70%; } 100% { width: 100%; } }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------
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

    st.markdown("---")
    st.caption("PaperScope — Summarize research papers quickly.")
    st.markdown("---")
    if DEMO_MODE:
        st.markdown("🟠 **Demo Mode Active**")
        st.caption("Summaries are generated from demo pipeline.")


# Page header
st.markdown('<div class="main-title">📚 PaperScope — Your AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Your personal assistant for academic research using LLMs</div>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Section: Search arXiv Papers
# ---------------------------------------------------------------------
if option == "🔍 Search arXiv Papers":
    st.header("🔍 Search arXiv Papers")
    keyword_input = st.text_input("Enter Keywords or Paper URL", placeholder="e.g., reinforcement learning for robots OR https://arxiv.org/abs/2301.12345")
    st.caption("💡 You can enter keywords to search arXiv, or paste a direct paper URL (arXiv or PDF link).")

    if st.button("🔎 Fetch & Summarize", key="fetch_summarize_btn"):
        if DEMO_MODE:
            st.info("This feature is disabled in Demo Mode. Please upload PDF or use demo content.")
        elif not keyword_input or keyword_input.strip() == "":
            st.warning("Please enter a keyword or URL to search.")
        else:
            # Loading placeholder
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔍 Fetching & summarizing... <span class="loading-dots"><span></span><span></span><span></span></span></div>
                        <div class="progress-bar-container"><div class="progress-bar"></div></div>
                    </div>
                """, unsafe_allow_html=True)

            try:
                data = fetch_and_summarize(keyword_input)
                loading_placeholder.empty()

                if not data:
                    st.info("No papers found or failed to fetch. Try a different query or URL.")
                else:
                    st.success(f"✅ Found and processed {len(data)} paper(s).")
                    # show up to last 10 results
                    for idx, item in enumerate(data[-10:][::-1]):
                        with st.expander(f"📄 {item.get('title', 'Untitled Paper')}"):
                            st.markdown("**Summary:**")
                            st.info(item.get("summary", "No summary available."))

                            # Prepare download options for this result
                            summary_text = item.get('summary', '')
                            md_bytes = f"# {item.get('title', 'Summary')}\n\n{summary_text}".encode("utf-8")
                            txt_bytes = summary_text.encode("utf-8")
                            # PDF generation metadata
                            metadata = {
                                "source": item.get('source', 'arXiv'),
                                "paper_id": item.get('id', 'N/A'),
                                "title": item.get('title', 'N/A')
                            }
                            pdf_buf = generate_pdf_from_text(title=item.get('title', 'PaperScope Summary'),
                                                             metadata=metadata,
                                                             body_text=summary_text,
                                                             annotations=item.get('annotations', ''))

                            dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
                            with dl_col1:
                                st.download_button(
                                    label="📄 Download TXT",
                                    data=txt_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                    mime="text/plain",
                                    key=f"download_txt_arxiv_{idx}"
                                )
                            with dl_col2:
                                st.download_button(
                                    label="📝 Download MD",
                                    data=md_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                    mime="text/markdown",
                                    key=f"download_md_arxiv_{idx}"
                                )
                            with dl_col3:
                                st.download_button(
                                    label="📘 Download PDF",
                                    data=pdf_buf,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                    mime="application/pdf",
                                    key=f"download_pdf_arxiv_{idx}"
                                )

            except Exception as e:
                loading_placeholder.empty()
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure the URL is valid or try a keyword search.")


# ---------------------------------------------------------------------
# Section: Query Stored Summaries
# ---------------------------------------------------------------------
elif option == "🧠 Query Stored Summaries":
    st.header("🧠 Query Stored Summaries")
    query_input = st.text_input("Search stored summaries", placeholder="e.g., contrastive learning")

    if st.button("🔍 Run Keyword Search", key="run_query_db"):
        if not query_input or query_input.strip() == "":
            st.warning("Please enter a search query.")
        else:
            placeholder = st.empty()
            with placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔍 Searching database <span class="loading-dots"><span></span><span></span><span></span></span></div>
                    </div>
                """, unsafe_allow_html=True)
            try:
                results = query_db(query_input)
                placeholder.empty()
                if not results:
                    st.info("No matching summaries found.")
                else:
                    st.success(f"✅ Found {len(results)} results.")
                    for idx, item in enumerate(results):
                        with st.expander(f"📄 {item.get('title', 'Untitled')}", expanded=(idx==0)):
                            st.markdown("**Summary:**")
                            st.info(item.get('summary', 'No summary available.'))

                            # Provide download buttons
                            download_col1, download_col2, download_col3 = st.columns([1,1,1])
                            summary_text = item.get('summary', '')
                            md_bytes = f"# {item.get('title', '')}\n\n{summary_text}".encode("utf-8")
                            txt_bytes = summary_text.encode("utf-8")
                            pdf_buf = generate_pdf_from_text(title=item.get('title', 'Summary'),
                                                             metadata={"id": item.get('id', '')},
                                                             body_text=summary_text,
                                                             annotations=item.get('annotations', ''))
                            with download_col1:
                                st.download_button(
                                    label="📄 TXT",
                                    data=txt_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                    mime="text/plain",
                                    key=f"query_txt_{idx}"
                                )
                            with download_col2:
                                st.download_button(
                                    label="📝 MD",
                                    data=md_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                    mime="text/markdown",
                                    key=f"query_md_{idx}"
                                )
                            with download_col3:
                                st.download_button(
                                    label="📘 PDF",
                                    data=pdf_buf,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                    mime="application/pdf",
                                    key=f"query_pdf_{idx}"
                                )

            except Exception as e:
                placeholder.empty()
                st.error(f"❌ Search failed: {str(e)}")


# ---------------------------------------------------------------------
# Section: Upload & Summarize PDF (MAIN: now with full download options)
# ---------------------------------------------------------------------
elif option == "📄 Upload & Summarize PDF":
    st.header("📄 Upload & Summarize PDF")
    st.caption("Upload a PDF research paper and get an AI-generated summary. Download the result as TXT / MD / PDF.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="uploader_main")

    if uploaded_file:
        # Save to a temp file for parser compatibility
        try:
            tmp_path = safe_write_temp_file(uploaded_file, filename="uploaded.pdf")
        except Exception as e:
            st.error(f"❌ Error saving uploaded file: {e}")
            st.stop()

        # Stage 1 - Extraction
        extraction_placeholder = st.empty()
        with extraction_placeholder.container():
            st.markdown("""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">📄 Extracting text from PDF<span class="loading-dots"><span></span><span></span><span></span></span></div>
                </div>
            """, unsafe_allow_html=True)

        try:
            extracted_text = extract_text_from_pdf(tmp_path)
        except Exception as e:
            extraction_placeholder.empty()
            st.error(f"❌ Extraction failed: {e}")
            st.info("Make sure PDF contains selectable text (not scanned images) or use OCR-enabled parsing.")
            st.stop()

        # Validate extracted text
        if not extracted_text or len(extracted_text.strip()) == 0:
            extraction_placeholder.empty()
            st.error("❌ No text extracted from PDF. The file may be scanned or encrypted.")
            st.stop()

        # Stage 2 - Summarization
        with extraction_placeholder.container():
            st.markdown("""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">🧠 Generating AI-powered summary<span class="loading-dots"><span></span><span></span><span></span></span></div>
                </div>
            """, unsafe_allow_html=True)

        try:
            summary_text = summarize(extracted_text)
        except Exception as e:
            extraction_placeholder.empty()
            st.error(f"❌ Summarization failed: {e}")
            st.stop()

        extraction_placeholder.empty()

        if not validate_summary(summary_text):
            st.error("❌ Generated an empty summary. Try again or adjust summarizer settings.")
            st.stop()

        # Display result
        st.subheader("📝 Generated Summary")
        st.success("Summary generated successfully.")
        st.markdown("**Summary:**")
        st.info(summary_text)

        # Save to history (optionally)
        try:
            history_entry = {
                "id": f"local-{uuid.uuid4().hex[:8]}",
                "title": uploaded_file.name,
                "abstract": "",  # abstract not available for uploads by default
                "summary": summary_text,
                "timestamp": datetime.now().isoformat(),
                "source": "upload",
                "annotations": ""
            }
            # Attempt to save history; if storage not configured, ignore gracefully
            try:
                save_history_entry(history_entry)
            except Exception:
                # If storage isn't implemented or errors out, continue without breaking UI
                pass
        except Exception:
            pass

        # Download options: TXT, MD, PDF (including richer PDF with metadata + annotations)
        st.markdown("---")
        st.markdown("### 📥 Download Your Summary")

        col_txt, col_md, col_pdf = st.columns(3)
        txt_bytes = summary_text.encode("utf-8")
        md_bytes = f"# {uploaded_file.name}\n\n{summary_text}".encode("utf-8")
        # Create rich PDF with metadata (filename, original timestamp)
        metadata = {
            "Original Filename": uploaded_file.name,
            "Generated On": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Source": "Uploaded PDF"
        }
        pdf_buffer = generate_pdf_from_text(title=uploaded_file.name, metadata=metadata, body_text=summary_text, annotations="")

        with col_txt:
            st.download_button(
                label="📄 Download TXT",
                data=txt_bytes,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.txt",
                mime="text/plain",
                key="download_upload_txt"
            )
        with col_md:
            st.download_button(
                label="📝 Download MD",
                data=md_bytes,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.md",
                mime="text/markdown",
                key="download_upload_md"
            )
        with col_pdf:
            st.download_button(
                label="📘 Download PDF",
                data=pdf_buffer,
                file_name=f"{safe_filename(uploaded_file.name)}_summary.pdf",
                mime="application/pdf",
                key="download_upload_pdf"
            )

        st.success("✅ PDF processed successfully!")

# ---------------------------------------------------------------------
# Section: Semantic Search (FAISS)
# ---------------------------------------------------------------------
elif option == "🔎 Semantic Search (FAISS)":
    st.header("🔎 Semantic Search (FAISS)")
    if st.button("🔄 Rebuild Index", key="rebuild_index_btn"):
        if DEMO_MODE:
            st.info("Index building is simulated in Demo Mode.")
        else:
            idx_placeholder = st.empty()
            with idx_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔄 Rebuilding semantic vector index<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    </div>
                """, unsafe_allow_html=True)
            try:
                build_index()
                idx_placeholder.empty()
                st.success("✅ Index rebuilt successfully.")
            except Exception as e:
                idx_placeholder.empty()
                st.error(f"❌ Failed to rebuild index: {e}")

    semantic_query = st.text_input("Enter a semantic query", placeholder="e.g., visual prompt tuning in robotics")
    if st.button("🔍 Search with FAISS", key="faiss_search_btn"):
        if not semantic_query or semantic_query.strip() == "":
            st.warning("Please enter a semantic query.")
        else:
            search_placeholder = st.empty()
            with search_placeholder.container():
                st.markdown("""
                    <div class="loading-container">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">🔎 Running semantic search<span class="loading-dots"><span></span><span></span><span></span></span></div>
                    </div>
                """, unsafe_allow_html=True)
            try:
                results = search_similar(semantic_query)
                search_placeholder.empty()
                if not results:
                    st.info("No similar results found.")
                else:
                    st.success(f"✅ Found {len(results)} similar items.")
                    for idx, item in enumerate(results):
                        with st.expander(f"📄 {item.get('title', 'Untitled')}", expanded=(idx==0)):
                            st.markdown("**Summary:**")
                            st.info(item.get('summary', 'No summary available.'))

                            download_col1, download_col2, download_col3 = st.columns([1,1,1])
                            summary_text = item.get('summary', '')
                            md_bytes = f"# {item.get('title', '')}\n\n{summary_text}".encode("utf-8")
                            txt_bytes = summary_text.encode("utf-8")
                            pdf_buf = generate_pdf_from_text(title=item.get('title', 'Summary'),
                                                             metadata={"id": item.get('id', '')},
                                                             body_text=summary_text,
                                                             annotations=item.get('annotations', ''))
                            with download_col1:
                                st.download_button(
                                    label="📄 TXT",
                                    data=txt_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.txt",
                                    mime="text/plain",
                                    key=f"faiss_txt_{idx}"
                                )
                            with download_col2:
                                st.download_button(
                                    label="📝 MD",
                                    data=md_bytes,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.md",
                                    mime="text/markdown",
                                    key=f"faiss_md_{idx}"
                                )
                            with download_col3:
                                st.download_button(
                                    label="📘 PDF",
                                    data=pdf_buf,
                                    file_name=f"{safe_filename(item.get('title', 'summary'))}.pdf",
                                    mime="application/pdf",
                                    key=f"faiss_pdf_{idx}"
                                )

            except Exception as e:
                search_placeholder.empty()
                st.error(f"❌ Semantic search failed: {e}")

# ---------------------------------------------------------------------
# Section: History
# ---------------------------------------------------------------------
elif option == "📚 History":
    st.header("📚 Summary History")
    st.markdown("View, filter, and download previously processed papers.")
    try:
        history = get_history() or []
    except Exception:
        # If storage unsupported, set empty
        history = []

    # Stats
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

    # Controls
    col_filter, col_sort, col_action = st.columns([3, 2, 1])
    with col_filter:
        search_filter = st.text_input("🔍 Filter by title or keyword", placeholder="Type to filter...")
    with col_sort:
        sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title A-Z"])
    with col_action:
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.session_state.get("confirm_clear", False):
                try:
                    clear_history()
                    st.success("History cleared!")
                    st.session_state.confirm_clear = False
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to clear history: {e}")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm clear all history")

    st.markdown("---")

    if not history:
        st.info("📭 No papers in history yet. Start by searching or uploading papers!")
    else:
        # Apply filters
        filtered = history
        if search_filter and search_filter.strip():
            q = search_filter.lower()
            filtered = [
                item for item in filtered
                if q in (item.get('title', '').lower() + item.get('abstract', '').lower() + item.get('summary', '').lower())
            ]

        # Sorting
        if sort_order == "Newest First":
            filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''), reverse=True)
        elif sort_order == "Oldest First":
            filtered = sorted(filtered, key=lambda x: x.get('timestamp', ''))
        elif sort_order == "Title A-Z":
            filtered = sorted(filtered, key=lambda x: x.get('title', '').lower())

        st.caption(f"Showing {len(filtered)} paper(s)")
        for idx, item in enumerate(filtered):
            with st.expander(f"📄 {item.get('title', 'Untitled Paper')}", expanded=(idx == 0)):
                top_col1, top_col2, top_col3 = st.columns([4, 1, 1])
                
                with top_col1:
                    timestamp = item.get('timestamp', 'Unknown date')
                    if timestamp and timestamp != "Unknown date":
                        try:
                            # ✅ Replace parse_iso with datetime.fromisoformat
                            ts = datetime.fromisoformat(timestamp)
                            timestamp = ts.strftime("%B %d, %Y at %I:%M %p")
                        except ValueError:
                            pass  # fallback: keep original string if parsing fails
                    st.caption(f"📅 Added: {timestamp}")
                    st.caption(f"🆔 ID: `{item.get('id', 'N/A')}`")
                with top_col2:
                    # prepare summary for download
                    summary_text = f"Title: {item.get('title', 'N/A')}\n\n"
                    summary_text += f"Abstract:\n{item.get('abstract', 'N/A')}\n\n"
                    summary_text += f"Summary:\n{item.get('summary', 'N/A')}\n\n"
                    txt_bytes = summary_text.encode("utf-8")
                    md_content = f"# {item.get('title', '')}\n\n**Abstract:**\n\n{item.get('abstract','')}\n\n**Summary:**\n\n{item.get('summary','')}"
                    md_bytes = md_content.encode("utf-8")
                    pdf_buf = generate_pdf_from_text(title=item.get('title', 'History Entry'),
                                                     metadata={"id": item.get('id', ''), "added_on": item.get('timestamp', '')},
                                                     body_text=item.get('summary', ''),
                                                     annotations=item.get('annotations', ''))
                    st.download_button(
                        label="📥 Download",
                        data=txt_bytes,
                        file_name=f"{safe_filename(item.get('id', 'paper'))}_summary.txt",
                        mime="text/plain",
                        key=f"history_download_{idx}",
                        help="Download summary as TXT"
                    )

                with top_col3:
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete this paper", type="secondary"):
                        try:
                            if delete_entry(item.get('id')):
                                st.success("Paper deleted!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete paper from storage.")
                        except Exception as e:
                            st.error(f"Error deleting entry: {e}")

                st.markdown("---")
                st.markdown("**Abstract:**")
                st.markdown(f"> {item.get('abstract', 'No abstract available.')}")
                st.markdown("**Summary:**")
                st.info(item.get('summary', 'No summary available.'))
                # arXiv link (if applicable)
                paper_id = item.get('id', '')
                if paper_id and ('arxiv' in paper_id.lower() or '/' in paper_id):
                    arxiv_id = paper_id.split('/')[-1] if '/' in paper_id else paper_id
                    st.markdown(f"🔗 [View on arXiv](https://arxiv.org/abs/{arxiv_id})")

# ---------------------------------------------------------------------
# Helper functions used inside UI blocks
# ---------------------------------------------------------------------
def safe_filename(name: str) -> str:
    """Create a filesystem-friendly filename from a title."""
    if not name:
        return "file"
    keepchars = (" ", ".", "_", "-")
    fname = "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()
    fname = fname.replace(" ", "_")[:200]
    return fname


def parse_iso(iso_str: str) -> datetime:
    """Parse ISO timestamp robustly, returning epoch if fails."""
    if not iso_str:
        return datetime.fromtimestamp(0)
    try:
        # many of your entries use fromisoformat style timestamps
        return datetime.fromisoformat(iso_str)
    except Exception:
        try:
            # fallback parse common formats
            return datetime.strptime(iso_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.fromtimestamp(0)


def to_date(iso_str: str) -> Optional[datetime.date]:
    try:
        return parse_iso(iso_str).date()
    except Exception:
        return None


# ---------------------------------------------------------------------
# End of file
# ---------------------------------------------------------------------
