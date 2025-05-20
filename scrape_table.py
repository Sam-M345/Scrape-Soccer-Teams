from pathlib import Path

# Removed project_root, scraper_module_path, and sys.path.insert lines
# as fetch.py is now expected to be in the same directory or Python path.

try:
    from fetch import fetch_html
    from parse import parse_valuations # Import for parsing
except ImportError as e:
    print(f"Error: Could not import necessary functions. {e}")
    print("Ensure fetch.py and parse.py are in the same directory or accessible in PYTHONPATH.")
    import sys 
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

CNBC_URL = "https://www.cnbc.com/2025/05/05/cnbcs-official-global-soccer-team-valuations-2025.html"
OUTPUT_CSV_FILENAME = "soccer_teams.csv"
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_CSV_PATH = PROJECT_ROOT / OUTPUT_CSV_FILENAME

def process_valuations():
    print(f"Attempting to download and parse valuations from: {CNBC_URL}")
    try:
        html_content = fetch_html(CNBC_URL)
        if html_content:
            print("HTML content fetched successfully. Attempting to parse...")
            df_valuations = parse_valuations(html_content)
            
            if df_valuations is not None and not df_valuations.empty:
                df_valuations.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')
                print(f"Successfully parsed and saved valuations to: {OUTPUT_CSV_PATH}")
                print(f"DataFrame shape: {df_valuations.shape}")
            elif df_valuations is None:
                print("Parsing returned None. Could not create DataFrame.")
            else: # DataFrame is empty
                print("Parsing resulted in an empty DataFrame. No data saved to CSV.")
        else:
            print("Failed to fetch HTML content. No content to parse.")
    except Exception as e:
        print(f"An error occurred during the process: {e}")

if __name__ == "__main__":
    process_valuations() 