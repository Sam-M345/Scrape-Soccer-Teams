from pathlib import Path
import pandas as pd
import os # Import os module for clearing screen

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
OUTPUT_CSV_FILENAME = "Scraped.csv"
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_CSV_PATH = PROJECT_ROOT / OUTPUT_CSV_FILENAME

# Imports for Rich table display
from rich.console import Console
from rich.table import Table

def process_valuations():
    os.system('cls') # Clear the terminal screen on Windows
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

                # Display the DataFrame as a Rich table
                console = Console(record=True) # Enable recording for HTML export
                rich_table = Table(title="Soccer Club Valuations", show_header=True, header_style="bold magenta", show_lines=True)

                # Define column styles for better readability (optional)
                # Example: Right-align numeric columns, left-align text
                column_styles = {
                    'rank': {"justify": "left", "style": "dim"},
                    'team': {"justify": "left"},
                    'country': {"justify": "left"},
                    'league': {"justify": "left"},
                    'value_usd_bln': {"justify": "left"},
                    'revenue_usd_bln': {"justify": "left"},
                    'ebitda_usd_bln': {"justify": "left"},
                    'debt_pct_value': {"justify": "left"},
                    'owners': {"justify": "left", "overflow": "fold"} # Fold long text
                }
                float_format_cols = {
                    'value_usd_bln': '{:.3f}',
                    'revenue_usd_bln': '{:.3f}',
                    'ebitda_usd_bln': '{:.3f}',
                    'debt_pct_value': '{:.1f}%'
                }

                for col_name in df_valuations.columns:
                    style_args = column_styles.get(col_name, {})
                    rich_table.add_column(str(col_name).replace('_', ' ').title(), **style_args)

                for index, row in df_valuations.iterrows():
                    row_values_for_rich = []
                    for col_name in df_valuations.columns:
                        value = row[col_name]
                        if pd.isna(value):
                            row_values_for_rich.append("[dim cyan]N/A[/dim cyan]") # Using Rich markup for N/A
                        elif col_name in float_format_cols:
                            # Ensure value is float before formatting, handle potential strings if parsing was loose
                            try:
                                formatted_value = float_format_cols[col_name].format(float(value))
                                row_values_for_rich.append(formatted_value)
                            except ValueError:
                                row_values_for_rich.append(str(value)) # Fallback to string if not convertible
                        else:
                            row_values_for_rich.append(str(value))
                    rich_table.add_row(*row_values_for_rich)
                
                console.print("\nGlobal Teams 🌐:")
                console.print(rich_table)

                # Export the Rich table to an HTML file
                try:
                    html_output_filename = "rich_table_output.html"
                    html_output_path = PROJECT_ROOT / html_output_filename
                    console.save_html(str(html_output_path))
                    print(f"Rich table also saved to: {html_output_path}")
                except Exception as e_html:
                    print(f"Error saving Rich table as HTML: {e_html}")

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