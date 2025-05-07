import pandas as pd
from bs4 import BeautifulSoup
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text

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
            print(f"Could not convert monetary value '{val_num_str}' to float.")
            return None
    else: # Attempt to parse if it's just a number, assuming billions
        try:
            # Try to remove any currency symbols or non-numeric characters except dot and then convert
            cleaned_val_str = re.sub(r'[^\d.]', '', value_str_raw)
            if cleaned_val_str: # Ensure not empty after cleaning
                 return float(cleaned_val_str)
        except ValueError:
            pass # Fall through if not a simple number
    # If all parsing fails for monetary value
    # print(f"Could not parse monetary string: {value_str_raw}") # Optional: uncomment for debugging unparsed monetary values
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
            print(f"Could not convert percentage value '{match.group(1)}' to float.")
            return None
    else: # Attempt to parse if it's just a number (e.g. "0" meaning 0%)
        try:
            # Ensure it's not an empty string after strip before float conversion
            stripped_val = value_str_raw.strip()
            if stripped_val: 
                return float(stripped_val)
        except ValueError:
            pass # Fall through
    # If all parsing fails for percentage value
    # print(f"Could not parse percentage string: {value_str_raw}") # Optional: uncomment for debugging unparsed percentages
    return None

EXPECTED_COLUMNS = [
    'rank', 'team', 'country', 'league', 
    'value_usd_bln', 'revenue_usd_bln', 'ebitda_usd_bln', 
    'debt_pct_value', 'owners'
]

# VALUATION_ROW_RE was here, removed as it's unused

def parse_valuations(html: str) -> pd.DataFrame | None:
    """
    Parses the HTML content to extract the soccer team valuations table.

    Specifically targets an HTML table structure for valuations.

    Args:
        html: The HTML content as a string.

    Returns:
        A pandas DataFrame with columns defined in EXPECTED_COLUMNS,
        or None if parsing fails.
    """
    soup = BeautifulSoup(html, 'lxml')
    data_rows = []

    valuation_table = soup.find('table') 

    if valuation_table:
        print("Found an HTML table. Attempting to parse rows from it.")
        tbody = valuation_table.find('tbody')
        if not tbody:
            tbody = valuation_table # Handle cases where tbody might not be explicit but rows are direct children

        rows = tbody.find_all('tr')
        print(f"Found {len(rows)} rows in the table.")

        for i, row in enumerate(rows): # enumerate to get index for skipping header warning
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

                    # Attempt to parse rank, skip row on failure here as it's critical
                    rank = int(re.sub(r'[^\d]', '', rank_str))
                    
                    team = team_str
                    country = country_str
                    league = league_str
                    owners = owners_str
                    
                    value_usd_bln = parse_monetary_value_to_billions(value_raw)
                    revenue_usd_bln = parse_monetary_value_to_billions(revenue_raw)
                    ebitda_usd_bln = parse_monetary_value_to_billions(ebitda_raw)
                    debt_pct_value = parse_percentage_value(debt_pct_raw)
                    
                    # Basic check: if rank is parsed and team name exists, proceed
                    # Rank is already an int here or ValueError would have been raised.
                    if team: 
                        is_duplicate = False
                        for r_data in data_rows:
                            if r_data[0] == rank or r_data[1].lower() == team.lower():
                                is_duplicate = True
                                # print(f"Skipping duplicate: Rank {rank} / Team {team}") # Optional: uncomment for debugging duplicates
                                break
                        if not is_duplicate:
                            data_rows.append((
                                rank, team, country, league,
                                value_usd_bln, revenue_usd_bln, ebitda_usd_bln,
                                debt_pct_value, owners
                            ))
                    else:
                        # This case (empty team name with valid rank) is unlikely if rank parsing succeeded
                        print(f"Skipping row due to empty team name. Rank: '{rank}', Team_str: '{team_str}'")

                except ValueError as e: # Specifically for rank int conversion failure
                    # This will catch the header row's RANK text and skip it, which is desired.
                    if i > 0: # Only print warning for non-header rows failing rank conversion
                         print(f"Skipping data row due to ValueError (likely rank '{cells[0].get_text(strip=True)}'): {e}")
                except Exception as e:
                    print(f"Skipping row due to unexpected error: {e} - Row index: {i} - Cells: {[c.get_text(strip=True) for c in cells]}" )
            elif i > 0: # If not enough cells and not the header row (i=0 assumed as header)
                print(f"Skipping data row {i+1}, not enough cells: {len(cells)} found, expected 9. Content: {[c.get_text(strip=True) for c in cells]}")
        
        if data_rows:
            print(f"Extracted {len(data_rows)} data rows from the HTML table.")
        else:
            print("No data rows extracted from the HTML table. Check selectors or table structure.")
    else:
        print("No HTML table found on the page. Cannot parse valuations.")

    if data_rows:
        df = pd.DataFrame(data_rows, columns=EXPECTED_COLUMNS)
        # Convert types, coercing errors for numeric to allow NaN for unparseable values
        df['rank'] = df['rank'].astype(int) # Rank should always be int
        
        numeric_cols = ['value_usd_bln', 'revenue_usd_bln', 'ebitda_usd_bln', 'debt_pct_value']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce') # Results in float64 or NaN
            
        # Ensure string columns are explicitly string type, handling potential None from parsing
        string_cols = ['team', 'country', 'league', 'owners']
        for col in string_cols:
            df[col] = df[col].astype(str).replace('None', '') # Replace NoneType converted to "None" string with empty string
            
        df.sort_values(by='rank', inplace=True)
        df.drop_duplicates(subset=['rank'], keep='first', inplace=True)
        df.drop_duplicates(subset=['team'], keep='first', inplace=True) 
        print("Successfully parsed data into DataFrame.")
        return df

    print("\nFailed to parse DataFrame or DataFrame is empty.")
    return None

if __name__ == '__main__':
    # Correctly locate the script's directory and navigate to the project root then to tests/data
    # Assuming parse.py is in soccer_scraper/ and this script is run from soccer_scraper directory or project root
    try:
        script_dir = Path(__file__).resolve().parent
        sample_html_file = script_dir.parent / "tests" / "data" / "sample_article.html"
        if not sample_html_file.exists(): # Fallback for direct execution from project root
            sample_html_file = Path(".") / "tests" / "data" / "sample_article.html"
    except NameError: # __file__ not defined (e.g. interactive) - use relative path
         sample_html_file = Path("tests/data/sample_article.html")

    if not sample_html_file.exists():
        print(f"Error: Sample HTML file not found at {sample_html_file}")
        print(f"Please ensure '{Path("tests/data/sample_article.html").resolve()}' exists.")
    else:
        print(f"Reading sample HTML from: {sample_html_file}")
        html_content = sample_html_file.read_text(encoding='utf-8')
        
        print("\nAttempting to parse valuations...")
        df_valuations = parse_valuations(html_content)
        
        if df_valuations is not None and not df_valuations.empty:
            # print("\nSuccessfully parsed DataFrame:") # Removed
            # pd.set_option('display.max_columns', None) # Keep commented, user can enable if needed
            # pd.set_option('display.width', 1000) # Keep commented, will set specifically for to_string
            # print(f"Shape: {df_valuations.shape}") # Removed
            # print("Data types:\n", df_valuations.dtypes) # Removed
            # print("\nFirst 5 rows:") # Removed
            # print(df_valuations.head()) # Removed

            print("\nFull table (formatted for console):\n")
            # pd.set_option('display.max_colwidth', None) # No longer needed for rich
            # pd.set_option('display.width', 2000)      # No longer needed for rich
            
            # # Use Styler to control alignment for both headers and data # Removed Styler logic
            # styled_df = df_valuations.style.set_properties(**{'text-align': 'left'})
            # styled_df = styled_df.set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}])
            # styled_df = styled_df.hide(axis='index') # Hides the default DataFrame index
            # print(styled_df.to_string())

            # --- Rich Table Output ---
            console = Console()
            rich_table = Table(show_header=True, header_style="bold magenta", show_lines=True, title="Soccer Club Valuations")

            float_columns_format = {
                'value_usd_bln': '{:.3f}',
                'revenue_usd_bln': '{:.3f}',
                'ebitda_usd_bln': '{:.3f}',
                'debt_pct_value': '{:.1f}'
            }

            for col_name in df_valuations.columns:
                justify_style = "right" if pd.api.types.is_numeric_dtype(df_valuations[col_name]) and col_name != 'rank' else "left"
                if col_name == 'rank': # Rank specifically right aligned for numbers but header left
                     rich_table.add_column(str(col_name), justify="right", style="dim") # Keep rank numbers right aligned
                else:
                     rich_table.add_column(str(col_name), justify=justify_style)

            for index, row in df_valuations.iterrows():
                row_values_for_rich = []
                for col_name in df_valuations.columns:
                    value = row[col_name]
                    if pd.isna(value):
                        row_values_for_rich.append(Text("N/A", style="dim cyan"))
                    elif col_name in float_columns_format:
                        row_values_for_rich.append(float_columns_format[col_name].format(value))
                    else:
                        row_values_for_rich.append(str(value))
                rich_table.add_row(*row_values_for_rich)
            
            console.print(rich_table)
            # --- End Rich Table Output ---

            # Save the DataFrame to CSV
            csv_output_path = script_dir.parent / "soccer_valuations.csv" # Save in project root
            if not sample_html_file.exists(): # if running from project root, script_dir.parent is not project root
                csv_output_path = Path(".") / "soccer_valuations.csv"
            try:
                df_valuations.to_csv(csv_output_path, index=False, encoding='utf-8')
                print(f"\nDataFrame successfully saved to: {csv_output_path.resolve()}")
            except Exception as e:
                print(f"\nError saving DataFrame to CSV: {e}")
            
            expected_rows = 25
            expected_cols = len(EXPECTED_COLUMNS)
            # Check shape
            if df_valuations.shape[0] == expected_rows and df_valuations.shape[1] == expected_cols:
                print(f"\nUS-2 Check (Shape): PASSED (found ({df_valuations.shape[0]},{df_valuations.shape[1]}), expected ({expected_rows},{expected_cols}))")
            else:
                print(f"\nUS-2 Check (Shape): FAILED or PARTIAL (found ({df_valuations.shape[0]},{df_valuations.shape[1]}), expected ({expected_rows},{expected_cols}))")

            # Check data types for key numeric columns
            type_checks_passed = True
            numeric_cols_to_check = ['value_usd_bln', 'revenue_usd_bln', 'ebitda_usd_bln', 'debt_pct_value']
            print("\nUS-3 Data Type Checks:")
            for col_name in numeric_cols_to_check:
                # Check if column exists and is float (NaNs are allowed in float columns)
                if col_name in df_valuations.columns and pd.api.types.is_numeric_dtype(df_valuations[col_name]) \
                   and (df_valuations[col_name].isnull().all() or pd.api.types.is_float_dtype(df_valuations[col_name].dropna())):
                    # Further check: if not all NaN, ensure it's float. If all NaN, it's fine as float.
                     actual_dtype = df_valuations[col_name].dtype
                     print(f"  - {col_name}: PASSED (is numeric, actual dtype: {actual_dtype})")
                else:
                    type_checks_passed = False
                    dt_info = df_valuations[col_name].dtype if col_name in df_valuations.columns else 'Column Missing'
                    print(f"  - {col_name}: FAILED (expected float, actual: {dt_info})")
            
            if type_checks_passed:
                print("All US-3 numeric type checks PASSED.")
            else:
                print("One or more US-3 numeric type checks FAILED.")
        else:
            print("\nFailed to parse DataFrame or DataFrame is empty.") 
            if df_valuations is None:
                 print("parse_valuations returned None.") 