# This python script joins multiple tables in a markdown file into a single csv file.
# It uses tkinter to prompt the user for a markdown file and a directory to save the output.
# It also uses loguru for logging and tqdm for progress indication.
import os
import sys
import re
import csv
import pandas as pd
from io import StringIO
from pandas import DataFrame
from loguru import logger
import streamlit as st

# Function to extract tables from markdown content
def extract_tables_from_markdown(content: str, filename: str = "file") -> list:
    lines = content.splitlines()
    dataframes = []
    expected_headers = ['ID', 'Name', 'Crew', 'Daily Output', 'Labor-Hours', 'Unit', 'Material', 'Labor', 'Equipment', 'Total', 'Total Incl O&P']

    last_section_code = ""
    last_section_name = ""
    i = 0
    table_count = 0
    while i < len(lines):
        line = lines[i]
        # Update last_section_code and last_section_name if this line is a markdown heading
        heading_match = re.match(r'^\s*#+\s+((?:\d{2,}\s+)*\d+\.\d+)\s+(.*)', line)
        if heading_match:
            current_section_code = heading_match.group(1).strip()
            # Check if the code is digits only (any length)
            if re.fullmatch(r'\d+', current_section_code):
                found = False
                for k in range(i-1, -1, -1):
                    prev_line = lines[k]
                    if re.match(r'^\|.*\|$', prev_line):
                        break
                    prev_heading_match = re.match(r'^\s*#+\s+([\d .]+)\s+(.*)', prev_line)
                    if prev_heading_match:
                        prev_code = prev_heading_match.group(1).strip()
                        if not re.fullmatch(r'\d+', prev_code):
                            last_section_code = prev_code
                            last_section_name = re.sub(r'^[-\s]+', '', prev_heading_match.group(2)).strip()
                            found = True
                            break
                if not found:
                    last_section_code = current_section_code
                    last_section_name = re.sub(r'^[-\s]+', '', heading_match.group(2)).strip()
            else:
                last_section_code = current_section_code
                last_section_name = re.sub(r'^[-\s]+', '', heading_match.group(2)).strip()
            i += 1
            continue
        elif re.match(r'^\s*#+\s+', line):
            # Heading without section code, keep last_section_code and update section name
            last_section_name = re.sub(r'^[-\s]+', '', line.lstrip('#')).strip()
            i += 1
            continue

        # Check if this line starts a markdown table
        if re.match(r'^\|.*\|$', line):
            # Collect all lines of the table
            table_lines = [line]
            j = i + 1
            while j < len(lines) and re.match(r'^\|.*\|$', lines[j]):
                table_lines.append(lines[j])
                j += 1

            # Remove separator line if present
            if len(table_lines) > 1 and re.match(r'^\|[-:| ]+\|$', table_lines[1]):
                table_lines.pop(1)

            rows = [[cell.strip() for cell in l.split('|')[1:-1]] for l in table_lines]
            max_cols = max(len(row) for row in rows)
            rows = [row + [''] * (max_cols - len(row)) for row in rows]

            headers = rows[0]
            table_count += 1
            if headers != expected_headers:
                preview_lines = '\n'.join([' | '.join(row) for row in rows[:6]])
                st.warning(f"Table {table_count} headers do not match expected.\nFound: {headers}\nExpected: {expected_headers}")
                st.text(f"First 3 lines of the table:\n{preview_lines}")
                user_headers = st.text_input(f"Enter comma-separated headers for Table {table_count} (or leave blank to use found headers)", value=", ".join(headers), key=f"header_input_{table_count}")
                if user_headers:
                    headers = [h.strip() for h in user_headers.split(',')]
                    rows[0] = headers

            # Add the section code and section name as the first two columns
            headers = ['Masterformat Section Code', 'Section Name'] + rows[0]
            data_rows = [[str(last_section_code), last_section_name] + row for row in rows[1:]]

            csv_data = StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(headers)
            for row in data_rows:
                csv_writer.writerow(row)
            csv_data.seek(0)
            df = pd.read_csv(csv_data, header=0, skip_blank_lines=True, dtype={'Masterformat Section Code': str})
            dataframes.append(df)

            i = j
        else:
            i += 1
    
    return dataframes

# Function to clean DataFrame
def clean_dataframe(df: DataFrame) -> DataFrame:
    # Ensure all columns are string type to avoid dtype issues when shifting
    df = df.astype(str)
    num_of_cells_to_shift = 4
    for index, row in df.iterrows():
        if pd.isna(row.iloc[-1]) or row.iloc[-1] == 'nan':
            df.iloc[index, -num_of_cells_to_shift:] = row.iloc[-num_of_cells_to_shift-1:-1].values
            df.iloc[index, -num_of_cells_to_shift-1] = ''

    return df

def streamlit_main():
    st.set_page_config(page_title="Markdown Table Combiner", layout="wide")
    st.title("Markdown Table Combiner")
    st.write("Upload one or more markdown files with tables to combine them into a single CSV.")

    uploaded_files = st.file_uploader("Choose Markdown file(s)", type=["md"], accept_multiple_files=True)
    output_dir = st.text_input("Output directory (absolute path)", value=os.getcwd())
    process_button = st.button("Process Markdown File(s)")

    if uploaded_files and output_dir and process_button:
        all_dataframes = []
        header_mismatch = False
        mismatch_details = []
        for uploaded_file in uploaded_files:
            content = uploaded_file.read().decode("utf-8")
            filename = uploaded_file.name
            extracted_dataframes = []
            lines = content.splitlines()
            expected_headers = ['ID', 'Name', 'Crew', 'Daily Output', 'Labor-Hours', 'Unit', 'Material', 'Labor', 'Equipment', 'Total', 'Total Incl O&P']
            last_section_code = ""
            last_section_name = ""
            i = 0
            table_count = 0
            while i < len(lines):
                line = lines[i]
                heading_match = re.match(r'^\s*#+\s+((?:\d{2,}\s+)*\d+\.\d+)\s+(.*)', line)
                if heading_match:
                    current_section_code = heading_match.group(1).strip()
                    if re.fullmatch(r'\d+', current_section_code):
                        found = False
                        for k in range(i-1, -1, -1):
                            prev_line = lines[k]
                            if re.match(r'^\|.*\|$', prev_line):
                                break
                            prev_heading_match = re.match(r'^\s*#+\s+([\d .]+)\s+(.*)', prev_line)
                            if prev_heading_match:
                                prev_code = prev_heading_match.group(1).strip()
                                if not re.fullmatch(r'\d+', prev_code):
                                    last_section_code = prev_code
                                    last_section_name = re.sub(r'^[-\s]+', '', prev_heading_match.group(2)).strip()
                                    found = True
                                    break
                        if not found:
                            last_section_code = current_section_code
                            last_section_name = re.sub(r'^[-\s]+', '', heading_match.group(2)).strip()
                    else:
                        last_section_code = current_section_code
                        last_section_name = re.sub(r'^[-\s]+', '', heading_match.group(2)).strip()
                    i += 1
                    continue
                elif re.match(r'^\s*#+\s+', line):
                    last_section_name = re.sub(r'^[-\s]+', '', line.lstrip('#')).strip()
                    i += 1
                    continue
                if re.match(r'^\|.*\|$', line):
                    table_lines = [line]
                    j = i + 1
                    while j < len(lines) and re.match(r'^\|.*\|$', lines[j]):
                        table_lines.append(lines[j])
                        j += 1
                    if len(table_lines) > 1 and re.match(r'^\|[-:| ]+\|$', table_lines[1]):
                        table_lines.pop(1)
                    rows = [[cell.strip() for cell in l.split('|')[1:-1]] for l in table_lines]
                    max_cols = max(len(row) for row in rows)
                    rows = [row + [''] * (max_cols - len(row)) for row in rows]
                    headers = rows[0]
                    table_count += 1
                    if headers != expected_headers:
                        header_mismatch = True
                        mismatch_details.append(f"File: {filename}, Table: {table_count}, Found: {headers}")
                        preview_lines = '\n'.join([' | '.join(row) for row in rows[:6]])
                        st.warning(f"Table {table_count} in {filename} headers do not match expected.\nFound: {headers}\nExpected: {expected_headers}")
                        st.text(f"First 3 lines of the table:\n{preview_lines}")
                    # Do not allow user to fix headers in this mode, just block export
                    headers = ['Masterformat Section Code', 'Section Name'] + rows[0]
                    data_rows = [[str(last_section_code), last_section_name] + row for row in rows[1:]]
                    csv_data = StringIO()
                    csv_writer = csv.writer(csv_data)
                    csv_writer.writerow(headers)
                    for row in data_rows:
                        csv_writer.writerow(row)
                    csv_data.seek(0)
                    df = pd.read_csv(csv_data, header=0, skip_blank_lines=True, dtype={'Masterformat Section Code': str})
                    extracted_dataframes.append(df)
                    i = j
                else:
                    i += 1
            # Clean up DataFrames
            cleaned_dfs = []
            for df in extracted_dataframes:
                cleaned_dfs.append(clean_dataframe(df))
            all_dataframes.extend(cleaned_dfs)
        if not all_dataframes:
            st.error("No tables found in the uploaded markdown files.")
            return
        if header_mismatch:
            st.error("Header mismatch detected in one or more tables. CSV export is disabled. Please fix the markdown files.")
            st.write("Details:")
            for detail in mismatch_details:
                st.write(detail)
            return
        combined_df = pd.DataFrame()
        for i, df in enumerate(all_dataframes):
            if combined_df.empty:
                combined_df = df
            else:
                combined_df = pd.concat([combined_df, df], ignore_index=True, sort=False)
        combined_df.reset_index(drop=True, inplace=True)
        st.success(f"Found {len(all_dataframes)} tables. Combined DataFrame shape: {combined_df.shape}")
        st.dataframe(combined_df.head(20))
        # Save to CSV
        output_file = os.path.join(output_dir, "combined_tables.csv")
        try:
            combined_df.to_csv(output_file, index=False, encoding='utf-8')
            st.success(f"Saved combined CSV to {output_file}")
            with open(output_file, "rb") as f:
                st.download_button("Download CSV", f, file_name=os.path.basename(output_file), mime="text/csv")
        except Exception as e:
            st.error(f"Failed to save CSV: {e}")

if __name__ == "__main__":
    streamlit_main()