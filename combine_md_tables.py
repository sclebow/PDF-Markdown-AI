# This python script joins multiple tables in a markdown file into a single csv file.
# It uses tkinter to prompt the user for a markdown file and a directory to save the output.
# It also uses loguru for logging and tqdm for progress indication.
import os
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog
from typing import List
from loguru import logger
from tqdm import tqdm
import re
import pandas as pd
from io import StringIO
import csv
from pandas import DataFrame

# Function to prompt the user for a markdown file and a directory to save the output
def prompt_for_file_and_directory() -> (str, str):
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    file_path = filedialog.askopenfilename(title="Select Markdown File", filetypes=[("Markdown files", "*.md")])
    if not file_path:
        logger.error("No file selected.")
        sys.exit(1)

    directory = filedialog.askdirectory(title="Select Output Directory")
    if not directory:
        logger.error("No directory selected.")
        sys.exit(1)

    return file_path, directory

# Function to extract tables from markdown content
def extract_tables_from_markdown(content: str, filename: str = "file") -> list:
    lines = content.splitlines()
    dataframes = []
    expected_headers = ['ID', 'Name', 'Crew', 'Daily Output', 'Labor-Hours', 'Unit', 'Material', 'Labor', 'Equipment', 'Total', 'Total Incl O&P']

    last_section_code = ""
    last_section_name = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        # Update last_section_code and last_section_name if this line is a markdown heading
        heading_match = re.match(r'^\s*#+\s*([\d.]+)\s+(.*)', line)
        if heading_match:
            last_section_code = heading_match.group(1).strip()
            last_section_name = heading_match.group(2).strip()
            i += 1
            continue
        elif re.match(r'^\s*#+\s+', line):
            # Heading without section code, reset section code and use heading as name
            last_section_code = ""
            last_section_name = line.lstrip('#').strip()
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
            if headers != expected_headers:
                import tkinter as tk
                from tkinter import simpledialog
                root = tk.Tk()
                root.withdraw()
                preview_lines = '\n'.join([' | '.join(row) for row in rows[:6]])
                user_headers = simpledialog.askstring(
                    f"{filename} - Table {len(dataframes)+1} Headers",
                    f"Headers do not match expected in file '{filename}', table {len(dataframes)+1}.\nFound: {headers}\nExpected: {expected_headers}\n\nFirst 3 lines of the table:\n{preview_lines}\n\nEnter comma-separated headers or leave blank to use found headers:"
                )
                if user_headers:
                    headers = [h.strip() for h in user_headers.split(',')]
                    rows[0] = headers

            # Add the section code and section name as the first two columns
            headers = ['Masterformat Section Code', 'Section Name'] + rows[0]
            data_rows = [[last_section_code, last_section_name] + row for row in rows[1:]]

            csv_data = StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(headers)
            for row in data_rows:
                csv_writer.writerow(row)
            csv_data.seek(0)
            df = pd.read_csv(csv_data, header=0, skip_blank_lines=True)
            dataframes.append(df)

            i = j
        else:
            i += 1

    return dataframes

# Function to save CSV content to a file
def save_csv_to_file(csv_content: str, output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    logger.info(f"Saved CSV content to {output_file}")

def process_markdown_file(file_path: str, output_directory: str) -> None:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract tables from markdown content, passing the filename
    extracted_dataframes = extract_tables_from_markdown(content, os.path.basename(file_path))
    logger.info(f"Found {len(extracted_dataframes)} tables in the markdown file.")
    
    for i, df in enumerate(extracted_dataframes):
        print()
        print(f'Table {i + 1} of {len(extracted_dataframes)}:')
        print("Headers:", df.columns.tolist())

    # Combine all DataFrames into a single DataFrame
    # Make sure to handle the case where headers are mismatched
    combined_df = pd.DataFrame()
    for i, df in enumerate(extracted_dataframes):
        if combined_df.empty:
            combined_df = df
        else:
            # Align columns by reindexing
            combined_df = pd.concat([combined_df, df], ignore_index=True, sort=False)

    # Reset index
    combined_df.reset_index(drop=True, inplace=True)

    # Save the combined DataFrame to a CSV file           
    output_file = os.path.join(output_directory, os.path.basename(file_path).replace('.md', '.csv'))
    combined_df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"Saved combined CSV to {output_file}")

if __name__ == "__main__":
    # Set up logging
    logger.add(sys.stderr, level="INFO", format="{time} {level} {message}")
    logger.info("Starting the markdown table extraction.")

    # Prompt for markdown file and output directory
    file_path, output_directory = prompt_for_file_and_directory()

    # Process the markdown file
    process_markdown_file(file_path, output_directory)

    logger.info("Markdown table extraction completed.")