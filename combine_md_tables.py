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
def extract_tables_from_markdown(content: str) -> List[str]:
    # Regular expression to match markdown tables
    table_regex = re.compile(r'(\|[^\n]+\|(?:\n\|[-:]+[-|:]*\|)+(?:\n\|[^\n]+\|)+)')
    tables = table_regex.findall(content)
    return tables

# Function to convert markdown table to CSV
def convert_markdown_table_to_csv(markdown_table: str) -> str:
    # Convert markdown table to CSV format
    csv_output = StringIO()
    reader = csv.reader(markdown_table.splitlines(), delimiter='|')
    writer = csv.writer(csv_output, quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        # Skip empty rows and rows with only whitespace
        if not any(cell.strip() for cell in row):
            continue
        # Write the row to the CSV output
        writer.writerow([cell.strip() for cell in row if cell.strip()])

    return csv_output.getvalue()

# Function to save CSV content to a file
def save_csv_to_file(csv_content: str, output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    logger.info(f"Saved CSV content to {output_file}")

# Function to process markdown file and save tables as CSV
def process_markdown_file(file_path: str, output_directory: str) -> None:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract tables from markdown content
    tables = extract_tables_from_markdown(content)
    logger.info(f"Found {len(tables)} tables in the markdown file.")

    # Process each table and save as CSV
    for i, table in enumerate(tables):
        csv_content = convert_markdown_table_to_csv(table)
        output_file = os.path.join(output_directory, f"table_{i + 1}.csv")
        save_csv_to_file(csv_content, output_file)
    logger.info(f"Processed {len(tables)} tables from {file_path} and saved to {output_directory}")

if __name__ == "__main__":
    # Set up logging
    logger.add(sys.stderr, level="INFO", format="{time} {level} {message}")
    logger.info("Starting the markdown table extraction.")

    # Prompt for markdown file and output directory
    file_path, output_directory = prompt_for_file_and_directory()

    # Process the markdown file
    process_markdown_file(file_path, output_directory)

    logger.info("Markdown table extraction completed.")