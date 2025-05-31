# This python script merges multiple markdown files into a single markdown file using a Streamlit GUI.
# It takes a directory path as input and merges all markdown files in that directory.

import os
import sys
from tqdm import tqdm
from loguru import logger
import streamlit as st
from typing import List

# Function to merge markdown files
def merge_markdown_files(directory: str, output_file: str, exclude_files: List[str] = None) -> int:
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
    return len(markdown_files)

# Streamlit GUI
def main():
    st.title("Markdown File Merger")
    st.write("This app merges all markdown (.md) files in a selected directory into a single markdown file.")

    directory = st.text_input("Enter the directory path containing markdown files:", value=os.getcwd())
    output_filename = st.text_input("Enter the output file name (without .md):", value="merged_output")

    exclude_files = st.text_area("Files to exclude (comma-separated):", value="")
    exclude_list = [f.strip() for f in exclude_files.split(",") if f.strip()]

    if st.button("Merge Markdown Files"):
        if not os.path.isdir(directory):
            st.error("Invalid directory path.")
            return
        if not output_filename:
            st.error("Please provide an output file name.")
            return
        output_file = os.path.join(directory, output_filename + ".md")
        with st.spinner("Merging files..."):
            num_files = merge_markdown_files(directory, output_file, exclude_list)
        st.success(f"Merged {num_files} files into {output_file}")
        st.download_button(
            label="Download merged markdown file",
            data=open(output_file, 'rb').read(),
            file_name=output_filename + ".md",
            mime="text/markdown"
        )

if __name__ == "__main__":
    logger.add(sys.stderr, level="INFO", format="{time} {level} {message}")
    logger.info("Starting the Streamlit markdown file merger.")
    main()