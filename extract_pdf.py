# This is a python script that extracts pages from a PDF file
# and saves them as separate PDF files and JPG images.
import PyPDF2
import os
import tkinter as tk
from tkinter import filedialog
from pdf2image import convert_from_path

start_page = 138
end_page = 182

# Prompt the user to select a PDF file
root = tk.Tk()
root.withdraw()  # Hide the root window
pdf_file_path = filedialog.askopenfilename(
    title="Select a PDF file",
    filetypes=[("PDF files", "*.pdf")]
)
if not pdf_file_path:
    print("No file selected. Exiting.")
    exit(1)
# Prompt the user to select a directory to save the extracted pages
output_dir = filedialog.askdirectory(
    title="Select a directory to save the extracted pages"
)
if not output_dir:
    print("No directory selected. Exiting.")
    exit(1)
# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
# Open the PDF file
with open(pdf_file_path, "rb") as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    # Check if the specified page range is valid
    if start_page < 0 or end_page > len(pdf_reader.pages):
        print(f"Invalid page range: {start_page} to {end_page}.")
        exit(1)
    # Extract the specified pages and save them as separate PDF files and JPG images
    for page_num in range(start_page, end_page):
        # Create PDF file
        pdf_writer = PyPDF2.PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_num])
        output_pdf_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
        with open(output_pdf_path, "wb") as output_pdf_file:
            pdf_writer.write(output_pdf_file)
        print(f"Extracted page {page_num + 1} to {output_pdf_path}")
        
        # Create JPG file from the extracted PDF
        try:
            # Convert the single-page PDF to an image
            images = convert_from_path(output_pdf_path)
            output_jpg_path = os.path.join(output_dir, f"page_{page_num + 1}.jpg")
            # Save the image as JPG
            images[0].save(output_jpg_path, 'JPEG')
            print(f"Converted page {page_num + 1} to {output_jpg_path}")
        except Exception as e:
            print(f"Error converting page {page_num + 1} to JPG: {e}")

print("All pages extracted successfully.")
# Close the root window
root.destroy()