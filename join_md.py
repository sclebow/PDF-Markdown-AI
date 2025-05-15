# This python script merges multiple markdown files into a single markdown file.
# It takes a directory path as input and merges all markdown files in that directory.

import os
import sys
from tqdm import tqdm
from loguru import logger
import tkinter as tk
from tkinter import filedialog, simpledialog
from typing import List

# Prompt the user for a directory path and file name using a GUI
def prompt_for_directory_and_filename() -> (str, str):
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    directory = tk.filedialog.askdirectory(title="Select Directory")
    if not directory:
        logger.error("No directory selected.")
        sys.exit(1)

    filename = tk.simpledialog.askstring("Input", "Enter the output file name (without .md):")
    if not filename:
        logger.error("No file name provided.")
        sys.exit(1)

    return directory, os.path.join(directory, filename + ".md")

# Function to merge markdown files
def merge_markdown_files(directory: str, output_file: str, exclude_files: List[str] = None) -> None:
    if exclude_files is None:
        exclude_files = []

    # Get all markdown files in the directory
    markdown_files = [f for f in os.listdir(directory) if f.endswith('.md') and f not in exclude_files]

    # Sort files by modification time
    markdown_files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))

    # Create a new markdown file to write the merged content
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in tqdm(markdown_files, desc="Merging files", unit="file"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(content + "\n\n")  # Add double newline between files
    logger.info(f"Merged {len(markdown_files)} files into {output_file}")

if __name__ == "__main__":
    # Set up logging
    logger.add(sys.stderr, level="INFO", format="{time} {level} {message}")
    logger.info("Starting the markdown file merger.")

    # Prompt for directory and output file name
    directory, output_file = prompt_for_directory_and_filename()

    # Merge markdown files
    merge_markdown_files(directory, output_file)
    
    logger.info("Markdown file merger completed.")