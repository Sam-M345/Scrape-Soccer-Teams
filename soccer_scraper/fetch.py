import requests
from requests import HTTPError

def fetch_html(url: str, timeout: int = 10) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # This is the core network call that retrieves the HTML from the URL
        r = requests.get(url, timeout=timeout, headers=headers)
        r.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return r.text
    except HTTPError as http_err:
        # In a real app, you might want to log this or raise a custom exception
        print(f"HTTP error occurred: {http_err}") 
        raise
    except Exception as err:
        # In a real app, you might want to log this or raise a custom exception
        print(f"Other error occurred: {err}")
        raise 