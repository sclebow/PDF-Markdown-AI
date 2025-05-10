# This Python script takes a pdf file, 
# then removes the OCR text from the pdf file, 
# then uses pytesseract to extract text from the pdf file,
# and finally saves the extracted text to a markdown file.

# Import libraries
import os
import pytesseract
import tkinter as tk
from tkinter import filedialog
from pdf2image import convert_from_path
from PIL import Image, ImageFilter
import traceback

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin"

directory = r"C:\Users\scleb\Documents\bimsc25\GitHub\PDF-Markdown-AI\test_pdfs"

def prompt_user_for_directory(root, title="Select Directory"):
    # Use a file dialog to get the directory to save markdown files
    markdown_directory = filedialog.askdirectory(
        title=title,
    )
    
    # If user cancels the dialog
    if not markdown_directory:
        print("No directory selected. Exiting.")
        return
    
    return markdown_directory

# Main function
def main():
    # Create a root window
    root = tk.Tk()
    
    # # Prompt the user for the file path of the PDF files
    # pdf_directory = prompt_user_for_directory(root, "Select Directory with PDF Files")
    # if not pdf_directory:
    #     return

    # # Prompt the user for the directory to save the markdown files
    # markdown_directory = prompt_user_for_directory(root, "Select Directory to Save Markdown Files")
    # if not markdown_directory:
    #     return

    pdf_directory = directory
    markdown_directory = os.path.join(directory, "outputs")
    
    # Destroy the root window
    root.destroy()

    # Get the list of pdf files in the directory
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
    if not pdf_files:
        print("No PDF files found in the directory.")
        return
        
    # Loop through each pdf file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
            text = ""
            for i, image in enumerate(images):
                # Increase the sharpness of the image
                image = image.convert("L")  # Convert to grayscale
                # image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize the image
                image = image.filter(ImageFilter.SHARPEN)  # Apply sharpen filter
                # image = image.resize((image.width * 2, image.height * 2), Image.ANTIALIAS)  # Upscale the image

                # Increase the contrast of the image
                image = image.point(lambda p: p * 1.5)  # Increase contrast
                # image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))  # Apply unsharp mask
                # image = image.filter(ImageFilter.SMOOTH_MORE)  # Apply smooth filter
                image = image.filter(ImageFilter.DETAIL)  # Apply detail filter
                # image = image.filter(ImageFilter.EDGE_ENHANCE)  # Apply edge enhance filter

                # Save the image to a jpg file
                image_file_name = os.path.splitext(pdf_file)[0] + f"_page_{i+1}.jpg"
                image_path = os.path.join(markdown_directory, image_file_name)
                image.save(image_path, 'JPEG')
                print(f"Saved {image_file_name} to {markdown_directory}")

                # OCR each image (page)
                page_text = pytesseract.image_to_string(image)
                text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
            print("Traceback:")
            traceback.print_exc()
            continue

        # Construct the markdown file name
        markdown_file_name = os.path.splitext(pdf_file)[0] + '.md'
        markdown_path = os.path.join(markdown_directory, markdown_file_name)

        # Save the extracted text to a markdown file
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"Extracted text from {pdf_file} and saved to {markdown_file_name}")

if __name__ == "__main__":
    main()
