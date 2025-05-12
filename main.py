# This is a python script that takes a large PDF file and splits it into smaller chunks.
# Then it converts each chunk into markdown format, by sending the text to OpenAI's GPT model.

# Import libraries
import os
import openai
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import base64
import datetime
import pytesseract
import cv2
import numpy as np
from google.cloud import vision

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin"

def extract_text_with_google_vision(image_path):
    """
    Use Google Cloud Vision OCR to extract text from the image.
    """
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    output = ""

    print("Texts:")
    for text in texts:
        print(f'\n"{text.description}"')
        vertices = (['({},{})'.format(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices])
        print('bounds: {}'.format(','.join(vertices)))
        
        output += text.description + "\n"

    print(f'Extracted text from {image_path}:\n{text}')

    return text

def preprocess_text(text):
    """
    Preprocess the text to remove unwanted strings
    and group lines of text.
    """
    # Remove "2022 Bare Costs" from the text
    # This is a specific requirement for the text extraction
    text = text.replace("2022 Bare Costs", "")

    # In general each line of the image should follow the same format
    # First there is a four digit integer that is the ID of the row
    # Then there is a string that is the name of the row
    # Then there is a sometimes a crew name, but not always
    # Then there is a series of numbers that are the values of the row

    # We first need to identify the ids
    # Then we can assume that the next string is the name of the row
    # Then we can assume that the next string is the crew name, unless it is a number
    # Then we can assume that all the strings after that are the values of the row until we reach the next id

    # Split the text into lines
    lines = text.split("\n")
    # Initialize a dictionary to hold the processed lines
    processed_lines = {}

    # Initialize a flag to indicate which id we are currently processing
    current_id = None

    # Iterate through each line
    for line in lines:
        # Strip leading and trailing whitespace
        line = line.strip()

        # Check if the line starts with a four digit number
        if len(line) == 4 and line.isdigit():
            # We have found a new row
            id = line
            current_id = id
            processed_lines[id] = {
                "name": "",
                "crew": "",
                "values": []
            }
        elif current_id is None:
            # We are processing the header or a blank line
            if "header" in processed_lines.keys():
                processed_lines["header"].append(line)
            else:
                processed_lines["header"] = [line]
        elif line.isdigit():
            # We have found a number, this is a value
            processed_lines[current_id]["values"].append(line)
        elif line:
            # We have found a string, this is the name or crew
            if processed_lines[current_id]["name"] == "":
                # This is the name
                processed_lines[current_id]["name"] = line
            elif processed_lines[current_id]["crew"] == "":
                # This is the crew
                processed_lines[current_id]["crew"] = line
            else:
                # This is an additional value
                processed_lines[current_id]["values"].append(line)

    # Now we need to convert the processed lines into a text format
    processed_text = ""
    for id, data in processed_lines.items():
        if id == "header":
            processed_text += "\n".join(data) + "\n"
        else:
            # Join the values with commas
            values = ", ".join(data["values"])
            # Create a line with the id, name, crew and values
            processed_text += f"{id}: {data['name']}, {data['crew']}, {values}\n"  

    return processed_text

def preprocess_image(image_path):
    """
    Preprocess the image for better OCR results.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Resize if too large
    if max(image.shape) > 2000:
        scale = 2000 / max(image.shape)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    # Apply adaptive thresholding
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 31, 2)
    # Denoise
    image = cv2.fastNlMeansDenoising(image, None, 30, 7, 21)
    return image

def extract_text_with_ocr(image_path):
    """
    Use Tesseract OCR to extract text from the image.
    """
    preprocessed = preprocess_image(image_path)
    # Save temp file for pytesseract
    temp_path = image_path + "_preprocessed.png"
    cv2.imwrite(temp_path, preprocessed)
    text = pytesseract.image_to_string(temp_path)
    os.remove(temp_path)
    return text

def convert_ocr_text_and_image_to_markdown(ocr_text, image_file_path, client, log_dir=None):
    """
    Sends both the OCR text and the original image to ChatGPT, instructing it to only arrange the OCR text into markdown,
    not to transcribe from the image.
    """
    with open(image_file_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    column_headers = [
        "ID",
        "Name",
        "Crew",
        "Daily Output",
        "Labor-Hours",
        "Unit",
        "Material",
        "Labor",
        "Equipment",
        "Total",
        "Total Incl O&P",
    ]

    prompt = (
        "You are given the OCR-extracted text from an image and the original image itself. "
        "Your task is to arrange the provided OCR text into markdown format, preserving any tables or structure. "
        "Do NOT transcribe or extract any new information from the image. "
        "Only use the provided OCR text. "
        "If the OCR text is unclear, leave it as is. "
        "Do not add, guess, or hallucinate any information. "
        "If a table contains blank or empty cells, preserve them as blank in the markdown table (do not fill or merge them). "
        "Keep the table structure and number of columns/rows as in the original text, even if some cells are empty. "
        f"The table columns are: {', '.join(column_headers)}. "
        "Provide only the markdown output, without any extra commentary or code blocks.\n\n"
        "OCR Text:\n"
        f"{ocr_text}"
    )

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0,
    )
    markdown_text = response.choices[0].message.content.strip()

    # Logging
    if log_dir is not None:
        log_file_path = os.path.join(log_dir, "conversion_log.txt")
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            log_file.write(f"Image: {image_file_path}\n")
            log_file.write("OCR Text:\n")
            log_file.write(ocr_text + "\n")
            log_file.write("Prompt:\n")
            log_file.write(prompt + "\n")
            log_file.write("GPT Markdown Output:\n")
            log_file.write(markdown_text + "\n")
            log_file.write("="*60 + "\n\n")

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

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

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

def calculate_patches(image_file_path):
    """
    Calculate the number of patches in the image file.
    
    Args:
        image_file_path (str): The path to the image file.
    
    Returns:
        int: The number of patches in the image.
    """
    # The number of patches is calculated based on the image size
    # Each patch is 32x32 pixels
    image = Image.open(image_file_path)
    width, height = image.size
    num_x_patches = (width + 32 - 1) // 32 # Ceiling division
    num_y_patches = (height + 32 - 1) // 32 # Ceiling division
    num_patches = num_x_patches * num_y_patches

    return num_patches

# Main function
def main():
    # Create a root window
    root = tk.Tk()

    # Read the OpenAI API key from the text file
    openai_key_file_path = os.path.join(os.path.dirname(__file__), "openai_key.txt")
    if os.path.exists(openai_key_file_path):
        with open(openai_key_file_path, 'r') as key_file:
            openai_api_key = key_file.read().strip()
    else:
        print("API key file not found. Please provide the API key manually.")
        openai_api_key = ""
    
    # Prompt the user to provide OpenAI API key using Tkinter
    openai_api_key = tk.simpledialog.askstring(
        "OpenAI API Key",
        "Enter your OpenAI API key:",
        initialvalue=openai_api_key
    )
    if not openai_api_key:
        print("No API key provided. Exiting.")
        return

    # Using TKinter, prompt the user to provide Google Cloud API json key
    google_cloud_key_file_path = os.path.join(os.path.dirname(__file__), "google_cloud_key.json")
    if os.path.exists(google_cloud_key_file_path):
        with open(google_cloud_key_file_path, 'r') as key_file:
            google_cloud_api_key = key_file.read().strip()
    else:
        print("Google Cloud API key file not found. Please provide the API key manually.")
        google_cloud_api_key = ""
    
    # Prompt the user to provide Google Cloud API key using Tkinter file dialog
    google_cloud_key_file_path = filedialog.askopenfilename(
        title="Select Google Cloud API Key File",
        filetypes=[("JSON files", "*.json")],
        initialdir=os.path.dirname(__file__)
    )

    # Set the environment variable for Google Cloud API key
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_cloud_key_file_path

    # Prompt the user for the file path of the image files
    image_directory = prompt_user_for_directory(root, "Select Directory with Image Files")
    if not image_directory:
        return

    # # Prompt the user for the directory to save the markdown files
    # markdown_directory = prompt_user_for_directory(root, "Select Directory to Save Markdown Files")
    # if not markdown_directory:
    #     return

    markdown_directory = image_directory  # Save markdown files in the same directory as images

    # Get the list of image files in the directory
    image_files = [f for f in os.listdir(image_directory) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("No image files found in the selected directory.")
        return
        
    client = openai.OpenAI(api_key=openai_api_key)

    # Loop through each image file and convert it to markdown
    # for image_file in image_files[:1]: # Limit to 1 file for testing
    for image_file in image_files:
        image_file_path = os.path.join(image_directory, image_file)

        # Check if the markdown file already exists
        markdown_file_name = os.path.splitext(image_file)[0] + ".md"
        markdown_file_path = os.path.join(markdown_directory, markdown_file_name)

        if os.path.exists(markdown_file_path):
            print(f"Markdown file {markdown_file_name} already exists. Skipping conversion.")
            continue

        # Calculate number of patches
        num_patches = calculate_patches(image_file_path)
        print(f"Number of patches in {image_file}: {num_patches}")

        # Confirm with the user before proceeding
        proceed = tk.messagebox.askyesno("Proceed?", f"Do you want to convert {image_file} to markdown?\nNumber of patches: {num_patches}")
        if not proceed:
            print("Conversion cancelled by user.")
            continue
        
        # Check if the file has already been processed with OCR
        ocr_text_file_path = os.path.join(markdown_directory, f"{os.path.splitext(image_file)[0]}_ocr.txt")
        processed_ocr_text_file_path = os.path.join(markdown_directory, f"{os.path.splitext(image_file)[0]}_processed_ocr.txt")

        if os.path.exists(ocr_text_file_path):
            print(f"OCR text file {ocr_text_file_path} already exists. Skipping OCR.")
            with open(ocr_text_file_path, 'r') as ocr_file:
                ocr_text = ocr_file.read()
        else:
            # Extract text using OCR
            ocr_text = extract_text_with_google_vision(image_file_path)

            # Save the OCR text to a file
            with open(ocr_text_file_path, 'w', encoding='utf-8') as ocr_file:
                ocr_file.write(ocr_text)
            print(f"Saved OCR text to {ocr_text_file_path}")
            
            # Preprocess the OCR text
            ocr_text = preprocess_text(ocr_text)

            # Save the processed OCR text to a file
            with open(processed_ocr_text_file_path, 'w', encoding='utf-8') as processed_ocr_file:
                processed_ocr_file.write(ocr_text)
            print(f"Saved processed OCR text to {processed_ocr_text_file_path}")

        print(f"OCR extracted text for {image_file}:\n{ocr_text}")

        # # Send OCR text and image to GPT for markdown formatting (arrange only, do not transcribe)
        # markdown_text = convert_ocr_text_and_image_to_markdown(
        #     ocr_text, image_file_path, client, log_dir=markdown_directory
        # )
        
        # # Save the markdown text to a file
        # save_markdown(markdown_text, markdown_file_path)
        
        # print(f"Converted {image_file} to {markdown_file_name}")

    # Print a message indicating that the process is complete
    print("All images converted to markdown successfully.")
    # Close the root window
    root.destroy()

if __name__ == "__main__":
    main()