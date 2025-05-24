# This is a Python script that joins multiple CSV files into a single CSV file.

import os
import pandas as pd
import argparse
import glob
import sys
import tkinter as tk
from tkinter import filedialog

# Prompt the user for the directory containing the CSV files using a GUI file dialog
def get_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory(title="Select Directory Containing CSV Files")
    if not directory:
        print("No directory selected. Exiting.")
        sys.exit(1)
    root.destroy()  # Close the root window
    return directory

# Function to join CSV files
def join_csv_files(directory):
    # Get a list of all CSV files in the directory
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    if not csv_files:
        print("No CSV files found in the selected directory.")
        return
    
    # Read and concatenate all CSV files into a single DataFrame
    combined_df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)

    # Remove duplicate rows
    combined_df.drop_duplicates(inplace=True)
    
    # Save the combined DataFrame to a new CSV file
    output_file = os.path.join(directory, 'combined.csv')
    combined_df.to_csv(output_file, index=False)
    
    print(f"Combined {len(csv_files)} CSV files into {output_file}")

# Main function
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Join multiple CSV files into a single CSV file.")
    parser.add_argument('-d', '--directory', type=str, help="Directory containing CSV files")
    
    # Parse arguments
    args = parser.parse_args()
    
    # If directory is not provided, prompt the user for it
    if not args.directory:
        args.directory = get_directory()
    
    # Join CSV files
    join_csv_files(args.directory)

if __name__ == "__main__":
    # Run the main function
    main()