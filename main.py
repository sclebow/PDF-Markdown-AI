# This is a python script that takes a large PDF file and splits it into smaller chunks.
# Then it converts each chunk into markdown format, by sending the text to OpenAI's GPT model.

# Import libraries
import os
import PyPDF2
import openai
import tkinter as tk
from tkinter import filedialog

# Define functions
def split_pdf(pdf_file_path, chunk_size, max_num_chunks=-1):
    """
    Splits a PDF file into smaller chunks based on the specified chunk size.
    
    Args:
        pdf_file_path (str): The path to the PDF file to be split.
        chunk_size (int): The number of pages in each chunk.
    
    Returns:
        list: A list of paths to the split PDF files.
    """
    # Create a PDF reader object
    with open(pdf_file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        
        # Create a list to store the paths of the split files
        split_files = []

        # Specify a directory to save the split files
        split_dir = os.path.dirname(pdf_file_path)
        sub_dir = os.path.join(split_dir, "split_files")
        
        # Split the PDF into smaller chunks
        if max_num_chunks > 0:
            total_pages = min(total_pages, max_num_chunks * chunk_size)
        for i in range(0, total_pages, chunk_size):
            writer = PyPDF2.PdfWriter()
            for j in range(i, min(i + chunk_size, total_pages)):
                writer.add_page(reader.pages[j])
            split_file_path = os.path.join(sub_dir, f"chunk_{i // chunk_size + 1}.pdf")
            with open(split_file_path, 'wb') as output_pdf:
                writer.write(output_pdf)
            split_files.append(split_file_path)
    
    return split_files
def convert_to_markdown(pdf_file_path):
    """
    Converts a PDF file to markdown format using OpenAI's GPT model.
    """
    # Read the PDF file
    with open(pdf_file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Use OpenAI's GPT model to convert the text to markdown
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Convert the following text to markdown:\n\n{text}"}
        ]
    )
    
    markdown_text = response['choices'][0]['message']['content']
    
    return markdown_text
def save_markdown(markdown_text, output_path):
    """
    Saves the markdown text to a file.
    
    Args:
        markdown_text (str): The markdown text to be saved.
        output_path (str): The path where the markdown file will be saved.
    """
    with open(output_path, 'w') as f:
        f.write(markdown_text)

def prompt_user_for_file(root):
    # Hide the root window
    root.withdraw()
    
    # Show the file dialog and get the selected file path
    pdf_file_path = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    
    # If user cancels the dialog
    if not pdf_file_path:
        print("No file selected. Exiting.")
        return
    
    return pdf_file_path

def prompt_user_for_directory(root):
    # Use a file dialog to get the directory to save markdown files
    markdown_directory = filedialog.askdirectory(
        title="Select Directory for Markdown Files"
    )
    
    # If user cancels the dialog
    if not markdown_directory:
        print("No directory selected. Exiting.")
        return
    
    return markdown_directory
def prompt_user_for_chunk_size(root):
    # Create a simple dialog to get the chunk size
    chunk_size = tk.simpledialog.askinteger(
        "Chunk Size",
        "Enter the number of pages per chunk:",
        minvalue=1,
        initialvalue=3
    )
    # If user cancels the dialog
    if chunk_size is None:
        print("No chunk size entered. Exiting.")
        return
    # If user enters an invalid chunk size
    if chunk_size <= 0:
        print("Invalid chunk size. Exiting.")
        return
    # Return the chunk size
    # Show the root window again
    root.deiconify()
    # Destroy the root window
    root.destroy()
    # Return the chunk size
    return chunk_size

# Main function
def main():
    # Create a root window
    root = tk.Tk()
    
    # Prompt the user for the file path of the PDF file
    pdf_file_path = prompt_user_for_file(root)
    if not pdf_file_path:
        return
    
    # Prompt the user for the directory to save the markdown files
    markdown_directory = prompt_user_for_directory(root)
    if not markdown_directory:
        return

    # Prompt the user for the chunk size
    chunk_size = prompt_user_for_chunk_size(root)

    # Check if the file exists
    if not os.path.exists(pdf_file_path):
        print("The specified PDF file does not exist.")
        return
    # Check if the directory exists
    if not os.path.exists(markdown_directory):
        print("The specified directory does not exist.")
        return
    # Check if the file is a PDF
    if not pdf_file_path.endswith('.pdf'):
        print("The specified file is not a PDF file.")
        return
    # Check if the chunk size is valid
    if chunk_size <= 0:
        print("The chunk size must be a positive integer.")
        return
    # Check if the directory is writable
    if not os.access(markdown_directory, os.W_OK):
        print("The specified directory is not writable.")
        return
    # Check if the file is readable
    if not os.access(pdf_file_path, os.R_OK):
        print("The specified PDF file is not readable.")
        return
    # Check if the file is a valid PDF
    try:
        with open(pdf_file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                print("The specified PDF file is empty.")
                return
    except PyPDF2.errors.PdfReadError:
        print("The specified file is not a valid PDF file.")
        return

    # Split the PDF file into smaller chunks
    split_files = split_pdf(pdf_file_path, chunk_size, max_num_chunks=5)

    print(f"Split the PDF file into {len(split_files)} chunks.")
    for i, split_file in enumerate(split_files[:5]):
        print(f"Chunk {i + 1}: {split_file}")

    # Convert each chunk into markdown format by sending the text to OpenAI's GPT model
    for i, split_file in enumerate(split_files):
        # Convert the chunk to markdown
        markdown_text = convert_to_markdown(split_file)
        
        # Save the markdown text to a file
        output_path = os.path.join(markdown_directory, f"chunk_{i + 1}.md")
        save_markdown(markdown_text, output_path)
        
        print(f"Converted {split_file} to {output_path}")

    # Save the markdown files to the specified directory

    # Print a message indicating that the process is complete

if __name__ == "__main__":
    main()