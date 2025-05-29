# This is a python script that extracts pages from a PDF file
# and saves them as separate PDF files and JPG images.
import PyPDF2
import os
import tkinter as tk
from tkinter import filedialog
from pdf2image import convert_from_path

start_page = 138
end_page = 182
page_offset = 14

# Add poppler installation path to system PATH
import sys
import os
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
if os.path.exists(poppler_path):
    if os.name == 'nt':
        os.environ['PATH'] += os.pathsep + poppler_path
    else:
        os.environ['PATH'] = poppler_path + os.pathsep + os.environ['PATH']

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

# Prompt user to select start and end pages using tkinter
# Create a simple dialog to get start and end pages from the user
def get_page_range():
    dialog = tk.Toplevel()
    dialog.title("Select Page Range")
    tk.Label(dialog, text="Start Page (1-based):").grid(row=0, column=0, padx=10, pady=5)
    start_var = tk.StringVar(value=str(start_page + 1))
    tk.Entry(dialog, textvariable=start_var).grid(row=0, column=1, padx=10, pady=5)
    tk.Label(dialog, text="End Page (1-based, inclusive):").grid(row=1, column=0, padx=10, pady=5)
    end_var = tk.StringVar(value=str(end_page + 1))
    tk.Entry(dialog, textvariable=end_var).grid(row=1, column=1, padx=10, pady=5)
    tk.Label(dialog, text="Page Offset:").grid(row=2, column=0, padx=10, pady=5)
    page_offset_var = tk.StringVar(value=str(page_offset))
    tk.Entry(dialog, textvariable=page_offset_var).grid(row=2, column=1, padx=10, pady=5)
    # Move the OK button to the bottom of the dialog
    tk.Label(dialog, text="Note: Page numbers are 1-based.").grid(row=3, column=0, columnspan=2, padx=10, pady=5)
    tk.Label(dialog, text="Page offset is added to the start and end pages.").grid(row=4, column=0, columnspan=2, padx=10, pady=5)
    result = {}

    def on_ok():
        try:
            s = int(start_var.get())
            e = int(end_var.get())
            p_o = int(page_offset_var.get())
            if s < 1 or e <= s:
                raise ValueError
            result['start'] = s - 1 + p_o
            result['end'] = e - 1 + p_o
            dialog.destroy()
        except Exception:
            tk.messagebox.showerror("Invalid Input", "Please enter valid page numbers.")

    tk.Button(dialog, text="OK", command=on_ok).grid(row=2, column=0, columnspan=2, pady=10)
    dialog.grab_set()
    root.wait_window(dialog)
    return result.get('start', start_page), result.get('end', end_page)

start_page, end_page = get_page_range()

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

def create_pdf_and_image(pdf_reader, page_num, output_dir):
    """Extracts a single page from the PDF and saves it as both a PDF and a JPG image.
    Args:
        pdf_reader (PyPDF2.PdfReader): The PDF reader object.
        page_num (int): The page number to extract (0-based index).
        output_dir (str): The directory to save the extracted files.
    Returns:
        None
    """
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

# Open the PDF file
with open(pdf_file_path, "rb") as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    # Check if the specified page range is valid
    if start_page < 0 or end_page > len(pdf_reader.pages):
        print(f"Invalid page range: {start_page} to {end_page}.")
        exit(1)
        
    # Extract the specified pages and save them as separate PDF files and JPG images
    for page_num in range(start_page, end_page):
        create_pdf_and_image(pdf_reader, page_num, output_dir)

print("All pages extracted successfully.")

# Close the root window
root.destroy()