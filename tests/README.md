# PaperScope Tests

## URL Fetching Tests

This test suite (`test_url_fetching.py`) demonstrates that the URL fetching functionality works correctly and isolates any issues to API credential problems.

### What is Tested

1. **URL Validation** - Verifies URLs are correctly identified (no credentials needed)
2. **arXiv ID Extraction** - Tests parsing of arXiv URLs (no credentials needed)
3. **PDF Download** - Tests downloading PDFs from URLs (no credentials needed)
4. **Complete Fetch Pipeline** - Tests the full paper fetching process

### Key Insights

The tests clearly show:
- ✅ URL validation works without any API credentials
- ✅ arXiv ID extraction works without any API credentials
- ✅ PDF downloading works without Gemini API credentials
- ✅ PDF text extraction works without any API credentials
- ❌ Only text summarization requires Gemini API credentials

### Running the Tests

```bash
# Run all tests with detailed output
python3 -m pytest tests/test_url_fetching.py -v

# Or run directly
python3 tests/test_url_fetching.py

# Run with unittest
python3 -m unittest tests.test_url_fetching -v
```

### Test Output

The tests will show:
- Which components work without credentials
- Where credential issues occur (only in summarization)
- That URL fetching logic is independent and functional

### Install Test Dependencies

```bash
pip3 install pytest pytest-cov
```

Or use unittest (built-in, no installation needed):
```bash
python3 -m unittest discover tests/
```
