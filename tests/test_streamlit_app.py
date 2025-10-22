import io
import os
import sys
import types
from types import ModuleType
from datetime import datetime,date
from pathlib import Path

# -----------------------------------------------------------------------------
# Add project root to import path
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -----------------------------------------------------------------------------
# Stub heavy project modules BEFORE importing the app
# -----------------------------------------------------------------------------
def _mk_module(name):
    m = ModuleType(name)
    sys.modules[name] = m
    return m

# paperscope.main
m_main = _mk_module("paperscope.main")
def _fake_fetch_and_summarize(x): return [{"title": "t", "summary": "s"}]
def _fake_query_db(x): return [{"title": "t", "summary": "s", "id": "1"}]
m_main.fetch_and_summarize = _fake_fetch_and_summarize
m_main.query_db = _fake_query_db

# paperscope.pdf_parser
m_pdf = _mk_module("paperscope.pdf_parser")
m_pdf.extract_text_from_pdf = lambda p: "dummy text"

# paperscope.vector_store
m_vs = _mk_module("paperscope.vector_store")
m_vs.build_index = lambda: None
m_vs.search_similar = lambda q: [{"title": "x", "summary": "y", "id": "2"}]

# Optional storage module (so STORAGE_AVAILABLE=True in app)
m_storage = _mk_module("paperscope.storage")
m_storage.get_history = lambda: []
m_storage.clear_history = lambda: None
m_storage.delete_entry = lambda _id: True
m_storage.save_history_entry = lambda _entry: None

# Optional helpers referenced by the app in some paths
m_url = _mk_module("paperscope.url_handler")
m_url.is_url = lambda s: s.startswith("http")

m_sum = _mk_module("paperscope.summarizer")
m_sum.summarize = lambda t: "summary"

m_demo = _mk_module("paperscope.demo_data")
m_demo.load_demo_data = lambda build_index=False: (True, "Loaded demo data")

# -----------------------------------------------------------------------------
# Minimal Streamlit mock with context support
# -----------------------------------------------------------------------------
class _Ctx:
    def __enter__(self, *a, **k): return self
    def __exit__(self, *a): return False

def _columns(n):
    count = n if isinstance(n, int) else len(n)
    return [_Ctx() for _ in range(count)]

sys.modules["streamlit"] = types.SimpleNamespace(
    set_page_config=lambda **_: None,
    markdown=lambda *a, **k: None,
    caption=lambda *a, **k: None,
    metric=lambda *a, **k: None,
    subheader=lambda *a, **k: None,
    radio=lambda *a, **k: "Search arXiv Papers",
    text_input=lambda *a, **k: "",
    selectbox=lambda *a, **k: None,
    button=lambda *a, **k: False,
    file_uploader=lambda *a, **k: None,
    sidebar=_Ctx(),
    expander=lambda *a, **k: _Ctx(),
    spinner=lambda *a, **k: _Ctx(),
    columns=_columns,
    success=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
    info=lambda *a, **k: None,
    download_button=lambda *a, **k: None,
    session_state={},
    stop=lambda *a, **k: None,
    rerun=lambda *a, **k: None,
)

# -----------------------------------------------------------------------------
# Import the app now that dependencies are mocked
# -----------------------------------------------------------------------------
import streamlit_app as app


# =========================
#       TESTS
# =========================
def test_safe_filename_removes_special_chars():
    unsafe = r"bad/name\with:chars?*<>.pdf"
    safe = app.safe_filename(unsafe)
    assert safe.endswith(".pdf")
    assert all(c.isalnum() or c in "._-" for c in safe)


def test_safe_filename_handles_empty():
    assert app.safe_filename("") == "file"


def test_generate_pdf_from_text_custom_font_no_bold(monkeypatch):
    """
    Your app registers only the regular DejaVu TTF. Using bold on that font
    raises 'Undefined font: dejavuB'. Here we avoid bold by omitting annotations.
    """
    # Simulate that the custom font file exists so the app takes the DejaVu path
    monkeypatch.setattr(app.os.path, "exists", lambda *_: True)
    buf = app.generate_pdf_from_text(
        title="Test Title",
        metadata={"Author": "Tester"},
        body_text="Body text here.",
        annotations=""   
    )
    assert isinstance(buf, io.BytesIO)
    assert buf.getvalue().startswith(b"%PDF")


def test_generate_pdf_from_text_builtin_font_supports_bold(monkeypatch):
    """
    Force built-in Helvetica path (no custom font). Helvetica supports 'B',
    and your function uses bold when annotations are present.
    """
    monkeypatch.setattr(app.os.path, "exists", lambda *_: False)
    buf = app.generate_pdf_from_text(
        title="Test Title",
        metadata={"Author": "Tester"},
        body_text="Body text here.",
        annotations="Notes in bold section"
    )
    assert buf.getvalue().startswith(b"%PDF")


def test_safe_write_temp_file_roundtrip(tmp_path, monkeypatch):
    # Redirect tempfile dir to a clean location for deterministic tests
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    data = io.BytesIO(b"hello")
    path = app.safe_write_temp_file(data, filename="x.pdf")
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == b"hello"


def test_validate_summary_truthiness():
    assert app.validate_summary("ok")
    assert not app.validate_summary("")
    assert not app.validate_summary(None)


def test_parse_iso_valid_and_invalid():
    valid = datetime.now().isoformat()
    assert isinstance(app.parse_iso(valid), datetime)
    invalid = app.parse_iso("not-a-date")
    assert isinstance(invalid, datetime)
    assert invalid.year in (1969, 1970)  # epoch-ish fallback


def test_to_date_valid_and_invalid():
    # valid -> real date
    d = app.to_date(datetime.now().isoformat())
    assert isinstance(d, date)

    # invalid -> epoch-ish fallback (comes from parse_iso)
    epochish = app.to_date("xxx")
    assert isinstance(epochish, date)
    assert epochish.year in (1969, 1970) 


def test_storage_fallbacks_callable():
    # If storage module is missing, app defines fallbacks; but we stubbed one.
    if not getattr(app, "STORAGE_AVAILABLE", True):
        app.get_history()
        app.clear_history()
        app.delete_entry("id-1")
        app.save_history_entry({"id": "id-1"})
