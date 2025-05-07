import pandas as pd
from bs4 import BeautifulSoup
import re

# Expected columns as per TDD plan, focusing on the required ones
# The actual HTML table might have more, we'll select these.
# The TDD doc specifically asks for ['rank','club','valuation_usd_bln']
EXPECTED_COLUMNS = ['rank', 'club', 'valuation_usd_bln'] 

# Regex to extract rank, club, and valuation based on the TDD plan's example:
# 1. Real Madrid — $6.7 billion
# This regex needs to be robust enough for variations.
# It will look for a number, a dot, team name, then a dollar value and "billion".
# We need to be careful with clubs having numbers in their names, though unlikely for top clubs.
# And valuations might be millions for some (though TDD implies billions).
# The TDD plan's own regex was: re.compile(r'^\s*(\d+)\.\s+(.+?)\s+—\s+\$([\d.]+)\s+billion')
# Let's adapt that.

VALUATION_ROW_RE = re.compile(r'^\s*(\d{1,2})\.?\s+(.+?)\s+\$([\d.]+)(B|M)', re.IGNORECASE) # Adjusted regex slightly
# A more general regex if the above is too specific, or if the table structure is different.
# Example: Looking for lines that start with a number (rank), then text (club), then a monetary value.
# This is a fallback and would require more careful parsing of the monetary value.

def parse_valuations(html: str) -> pd.DataFrame | None:
    """
    Parses the HTML content to extract the soccer team valuations table.

    Specifically targets an HTML table structure for valuations.

    Args:
        html: The HTML content as a string.

    Returns:
        A pandas DataFrame with columns ['rank', 'club', 'valuation_usd_bln'],
        or None if parsing fails.
    """
    soup = BeautifulSoup(html, 'lxml')
    data_rows = []

    # Strategy: Find the HTML table and parse its rows and cells
    # The target table is the main valuations table on the CNBC page.
    # <table class="TheTable-table-GqgO2hLS TheTable-tableOddEven-Gv26S_2h"> could be a selector if needed
    # For now, let's assume it's the most prominent table or the first one that matches a basic description.
    valuation_table = soup.find('table') 

    if valuation_table:
        print("Found an HTML table. Attempting to parse rows from it.")
        tbody = valuation_table.find('tbody')
        if not tbody:
            tbody = valuation_table # Handle cases where tbody might not be explicit but rows are direct children

        rows = tbody.find_all('tr')
        print(f"Found {len(rows)} rows in the table.")

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5: # Ensure enough cells for Rank, Team, Value
                try:
                    rank_str = cells[0].get_text(strip=True)
                    club_str = cells[1].get_text(strip=True) # Club name is in the second cell
                    # Value string is in the 5th cell (index 4), e.g., "$6.7B", "$930M"
                    value_str_raw = cells[4].get_text(strip=True)

                    # Clean and parse rank
                    rank = int(re.sub(r'[^\d]', '', rank_str)) # Ensure \d is used

                    # Clean club name (already stripped)
                    club = club_str

                    # Parse valuation from strings like "$6.7B" or "$930M"
                    value_match = re.search(r'\$([\d.]+)([BM])', value_str_raw, re.IGNORECASE) # Ensure \d is used
                    if value_match:
                        val_num_str, unit = value_match.groups()
                        valuation = float(val_num_str)
                        if unit.upper() == 'M':
                            valuation /= 1000.0  # Convert millions to billions
                        
                        # Check for duplicates based on rank or club to avoid reprocessing
                        is_duplicate = False
                        for r_data in data_rows:
                            if r_data[0] == rank or r_data[1].lower() == club.lower():
                                is_duplicate = True
                                print(f"Skipping duplicate: Rank {rank} / Club {club}")
                                break
                        if not is_duplicate:
                            data_rows.append((rank, club, valuation))
                    else:
                        print(f"Could not parse value string: {value_str_raw} for club {club}")

                except ValueError as e:
                    print(f"Skipping row due to ValueError (e.g., converting rank): {e} - Row data: {[c.get_text(strip=True) for c in cells]}" )
                except Exception as e:
                    print(f"Skipping row due to other error: {e} - Row data: {[c.get_text(strip=True) for c in cells]}" )
            # else:
                # print(f"Skipping row, not enough cells: {len(cells)}")
        
        if data_rows:
            print(f"Extracted {len(data_rows)} rows from the HTML table.")
        else:
            print("No data rows extracted from the HTML table. Check selectors or table structure.")
    else:
        print("No HTML table found on the page. Cannot parse valuations.")

    if data_rows:
        df = pd.DataFrame(data_rows, columns=EXPECTED_COLUMNS)
        df['rank'] = df['rank'].astype(int)
        df['valuation_usd_bln'] = df['valuation_usd_bln'].astype(float)
        df.sort_values(by='rank', inplace=True)
        df.drop_duplicates(subset=['rank'], keep='first', inplace=True) # Ensure unique ranks
        # Additional check for club name duplicates if rank isn't strictly unique or reliable
        df.drop_duplicates(subset=['club'], keep='first', inplace=True) 
        print("Successfully parsed data into DataFrame.")
        return df

    print("\nFailed to parse DataFrame or DataFrame is empty.")
    # Print what was attempted if df_valuations is None to help debug
    if df_valuations is None:
        print("parse_valuations returned None.")
    return None

if __name__ == '__main__':
    from pathlib import Path
    # Assuming this script is in soccer_scraper/soccer_scraper/
    # and sample_article.html is in soccer_scraper/tests/data/
    sample_html_file = Path(__file__).parent.parent / "tests" / "data" / "sample_article.html"
    
    if not sample_html_file.exists():
        print(f"Error: Sample HTML file not found at {sample_html_file}")
        print("Please ensure 'soccer_scraper/tests/data/sample_article.html' exists.")
    else:
        print(f"Reading sample HTML from: {sample_html_file}")
        html_content = sample_html_file.read_text(encoding='utf-8')
        
        print("\nAttempting to parse valuations...")
        df_valuations = parse_valuations(html_content)
        
        if df_valuations is not None and not df_valuations.empty:
            print("\nSuccessfully parsed DataFrame:")
            print(f"Shape: {df_valuations.shape}")
            print("Data types:\n", df_valuations.dtypes)
            print("\nFirst 5 rows:")
            print(df_valuations.head())
            
            # Check US-2: 25 rows (or at least a good number)
            if 20 <= len(df_valuations) <= 30: # Allow some flexibility
                print(f"\nUS-2 Check: PASSED (found {len(df_valuations)} rows, expected around 25)")
            else:
                print(f"\nUS-2 Check: FAILED or PARTIAL (found {len(df_valuations)} rows, expected around 25)")

            # Check US-3: valuation_usd_bln is float
            if 'valuation_usd_bln' in df_valuations.columns and pd.api.types.is_float_dtype(df_valuations['valuation_usd_bln']):
                print("US-3 Check (dtype): PASSED (valuation_usd_bln is float)")
            else:
                print("US-3 Check (dtype): FAILED (valuation_usd_bln is not float or column missing)")
        else:
            print("\nFailed to parse DataFrame or DataFrame is empty.") 