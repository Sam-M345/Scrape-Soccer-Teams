import pandas as pd
from bs4 import BeautifulSoup
import re

# Helper function to parse monetary values like $1.2B or $345M into billions
def parse_monetary_value_to_billions(value_str_raw: str) -> float | None:
    if not value_str_raw or value_str_raw.strip().upper() in ['N/A', '-', '']:
        return None
    match = re.search(r'\$([\d.]+)([BM])', value_str_raw, re.IGNORECASE)
    if match:
        val_num_str, unit = match.groups()
        try:
            valuation = float(val_num_str)
            if unit.upper() == 'M':
                valuation /= 1000.0  # Convert millions to billions
            return valuation
        except ValueError:
            # print(f"Could not convert monetary value '{val_num_str}' to float.") # Optional debug
            return None
    else: # Attempt to parse if it's just a number, assuming billions
        try:
            cleaned_val_str = re.sub(r'[^\d.]', '', value_str_raw)
            if cleaned_val_str:
                 return float(cleaned_val_str)
        except ValueError:
            pass
    return None

# Helper function to parse percentage values like 19% or 0%
def parse_percentage_value(value_str_raw: str) -> float | None:
    if not value_str_raw or value_str_raw.strip().upper() in ['N/A', '-', '']:
        return None
    match = re.search(r'([\d.]+)%', value_str_raw)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            # print(f"Could not convert percentage value '{match.group(1)}' to float.") # Optional debug
            return None
    else: # Attempt to parse if it's just a number (e.g. "0" meaning 0%)
        try:
            stripped_val = value_str_raw.strip()
            if stripped_val:
                return float(stripped_val)
        except ValueError:
            pass
    return None

EXPECTED_COLUMNS = [
    'rank', 'team', 'country', 'league',
    'value_usd_bln', 'revenue_usd_bln', 'ebitda_usd_bln',
    'debt_pct_value', 'owners'
]

def parse_valuations(html: str) -> pd.DataFrame | None:
    """
    Parses the HTML content to extract the soccer team valuations table.
    Args:
        html: The HTML content as a string.
    Returns:
        A pandas DataFrame with columns defined in EXPECTED_COLUMNS, or None if parsing fails.
    """
    soup = BeautifulSoup(html, 'lxml')
    data_rows = []
    valuation_table = soup.find('table')

    if not valuation_table:
        print("No HTML table found on the page. Cannot parse valuations.")
        return None

    # print("Found an HTML table. Attempting to parse rows from it.") # Optional debug
    tbody = valuation_table.find('tbody')
    if not tbody:
        tbody = valuation_table

    rows = tbody.find_all('tr')
    # print(f"Found {len(rows)} rows in the table.") # Optional debug

    for i, row in enumerate(rows):
        cells = row.find_all('td')
        if len(cells) >= 9: # Ensure enough cells for all 9 columns
            try:
                rank_str = cells[0].get_text(strip=True)
                team_str = cells[1].get_text(strip=True)
                country_str = cells[2].get_text(strip=True)
                league_str = cells[3].get_text(strip=True)
                value_raw = cells[4].get_text(strip=True)
                revenue_raw = cells[5].get_text(strip=True)
                ebitda_raw = cells[6].get_text(strip=True)
                debt_pct_raw = cells[7].get_text(strip=True)
                owners_str = cells[8].get_text(strip=True)

                rank = int(re.sub(r'[^\d]', '', rank_str))
                team = team_str
                country = country_str
                league = league_str
                owners = owners_str

                value_usd_bln = parse_monetary_value_to_billions(value_raw)
                revenue_usd_bln = parse_monetary_value_to_billions(revenue_raw)
                ebitda_usd_bln = parse_monetary_value_to_billions(ebitda_raw)
                debt_pct_value = parse_percentage_value(debt_pct_raw)

                if team:
                    is_duplicate = any(r_data[0] == rank or r_data[1].lower() == team.lower() for r_data in data_rows)
                    if not is_duplicate:
                        data_rows.append((
                            rank, team, country, league,
                            value_usd_bln, revenue_usd_bln, ebitda_usd_bln,
                            debt_pct_value, owners
                        ))
            except ValueError: # Catches rank int conversion failure (e.g., header)
                if i > 0: # Only print warning for non-header rows failing rank conversion
                    # print(f"Skipping data row due to ValueError (likely rank '{cells[0].get_text(strip=True)}')") # Optional debug
                    pass
            except Exception as e:
                # print(f"Skipping row due to unexpected error: {e}") # Optional debug
                pass
        elif i > 0 : # If not enough cells and not the header row
            # print(f"Skipping data row {i+1}, not enough cells: {len(cells)}") # Optional debug
            pass

    if not data_rows:
        # print("No data rows extracted from the HTML table.") # Optional debug
        return None

    df = pd.DataFrame(data_rows, columns=EXPECTED_COLUMNS)
    df['rank'] = df['rank'].astype(int)
    numeric_cols = ['value_usd_bln', 'revenue_usd_bln', 'ebitda_usd_bln', 'debt_pct_value']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    string_cols = ['team', 'country', 'league', 'owners']
    for col in string_cols:
        df[col] = df[col].astype(str).replace('None', '')

    df.sort_values(by='rank', inplace=True)
    df.drop_duplicates(subset=['rank'], keep='first', inplace=True)
    df.drop_duplicates(subset=['team'], keep='first', inplace=True)
    # print("Successfully parsed data into DataFrame.") # Optional debug
    return df 