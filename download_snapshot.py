from pathlib import Path
import sys

# Add the soccer_scraper directory to the Python path
# to allow importing from soccer_scraper.fetch
project_root = Path(__file__).resolve().parent
scraper_module_path = project_root / "soccer_scraper"
sys.path.insert(0, str(scraper_module_path.parent)) # Add parent of soccer_scraper to path

try:
    from soccer_scraper.fetch import fetch_html
except ImportError:
    print("Error: Could not import fetch_html. Ensure soccer_scraper package is accessible.")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

CNBC_URL = "https://www.cnbc.com/2025/05/05/cnbcs-official-global-soccer-team-valuations-2025.html"
SNAPSHOT_DIR = project_root / "tests" / "data"
SNAPSHOT_FILENAME = "sample_article.html"
SNAPSHOT_PATH = SNAPSHOT_DIR / SNAPSHOT_FILENAME

def create_snapshot():
    print(f"Attempting to download snapshot from: {CNBC_URL}")
    try:
        html_content = fetch_html(CNBC_URL)
        if html_content:
            # Ensure the tests/data directory exists
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            
            SNAPSHOT_PATH.write_text(html_content, encoding='utf-8')
            print(f"Successfully downloaded and saved snapshot to: {SNAPSHOT_PATH}")
            print(f"File size: {SNAPSHOT_PATH.stat().st_size / (1024*1024):.2f} MB")
        else:
            print("Failed to fetch HTML content. No content returned.")
    except Exception as e:
        print(f"An error occurred during snapshot creation: {e}")

if __name__ == "__main__":
    create_snapshot() 