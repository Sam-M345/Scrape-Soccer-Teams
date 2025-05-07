import pytest
import responses
import requests # Added for requests.exceptions.RequestException
from pathlib import Path
from soccer_scraper.soccer_scraper.fetch import fetch_html # Assuming fetch_html itself raises HTTPError from requests
from requests import HTTPError # To explicitly catch and test for it

# Determine the project root directory to construct absolute paths
TEST_DATA_DIR = Path(__file__).parent / "data"
SAMPLE_HTML_FILE = TEST_DATA_DIR / "sample_article.html"
TEST_URL = "https://www.cnbc.com/2025/05/05/cnbcs-official-global-soccer-team-valuations-2025.html" 

@pytest.fixture
def mock_successful_response():
    try:
        sample_html_content = SAMPLE_HTML_FILE.read_text(encoding='utf-8')
    except FileNotFoundError:
        pytest.fail(f"Test data file not found: {SAMPLE_HTML_FILE}. Ensure it exists in tests/data/")
    except Exception as e:
        pytest.fail(f"Error reading sample HTML file: {e}")

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, TEST_URL, body=sample_html_content, status=200)
        yield rsps

@pytest.fixture
def mock_failed_response():
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, TEST_URL, status=404) # Simulate a Not Found error
        yield rsps 

def test_fetch_html_success(mock_successful_response):
    """Test US-1: Fetch article successfully."""
    html_content = fetch_html(TEST_URL)
    assert html_content is not None
    assert html_content.strip().lower().startswith("<!doctype html")
    assert len(mock_successful_response.calls) == 1
    assert mock_successful_response.calls[0].request.url == TEST_URL

def test_fetch_html_http_error(mock_failed_response):
    """Test fetching with a simulated HTTP error (e.g., 404)."""
    with pytest.raises(HTTPError):
        fetch_html(TEST_URL)
    assert len(mock_failed_response.calls) == 1
    assert mock_failed_response.calls[0].request.url == TEST_URL

def test_fetch_html_network_error():
    """Test fetching with a network error (e.g., invalid URL, DNS failure)."""
    invalid_url = "http://thisurldoesnotexistforsure.invalid/"
    # We expect requests.exceptions.RequestException or one of its subclasses like ConnectionError
    with pytest.raises(requests.exceptions.RequestException):
        fetch_html(invalid_url) 