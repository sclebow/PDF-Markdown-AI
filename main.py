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
import cv2
import numpy as np
from google.cloud import vision
import pickle
import traceback
import concurrent.futures
import time

POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin"
GPT_MODEL = "gpt-4.1"  # Specify the GPT model to use

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
    
    # output = ""
    # vertices_list = []

    output = []

    # print("Texts:")
    for text in texts:
        # print(f'\n"{text.description}"')
        vertices = text.bounding_poly.vertices
        # print("Vertices:")
        vertices_for_this_text = []
        for vertex in vertices:
            # print(f"({vertex.x}, {vertex.y})")
            # Convert to a list of tuples
            vertices_for_this_text.append((vertex.x, vertex.y))
        
        output.append({
            "text": text.description,
            "vertices": vertices_for_this_text,
            "entity": text
        })

    # print(f"Full text: {output}")

    return output

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

def convert_ocr_lines_to_markdown(ocr_lines, client, log_dir, rate_limit_tpm=30000, tokens_per_call=14000, last_call_time=[0], calls_this_minute=[0]):
    """
    Convert OCR lines to markdown format using ChatGPT, with token-per-minute rate limiting and retry on rate limit errors.
    """
    max_retries = 10
    for attempt in range(max_retries):
        try:
            # Calculate the minimum interval between calls to stay under the TPM limit
            min_interval = 60 * tokens_per_call / rate_limit_tpm  # seconds
            now = time.time()
            # Enforce rate limit
            elapsed = now - last_call_time[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call_time[0] = time.time()
            # Convert lines to string
            ocr_text = "\n".join(ocr_lines)
            prompt = (
                "Your task is to arrange the provided OCR text into markdown format, preserving any tables or structure. "
                "Only use the provided OCR text. "
                "Add headers, line breaks, and other markdown formatting as needed. "
                "Remove any unnecessary spaces"
                "If the OCR text is unclear, leave it as is. "
                "Do not add, guess, or hallucinate any information. "
                "Determine if a table is present in the text. "
                "If a table is present, arrange the text into a markdown table, otherwise, return the text as is. "
                "- If a table contains blank or empty cells, preserve them as blank in the markdown table (do not fill or merge them). "
                "- Keep the table structure and number of columns/rows as in the original text, even if some cells are empty. "
                "- The table columns are: ID, Name, Crew, Daily Output, Labor-Hours, Unit, Material, Labor, Equipment, Total, Total Incl O&P. "
                "Provide only the markdown output, without any extra commentary or code blocks.\n\n"
                "OCR Text:\n"
                f"{ocr_text}\n\n"
            )
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
                    log_file.write("OCR Text:\n")
                    log_file.write(ocr_text + "\n")
                    log_file.write("Prompt:\n")
                    log_file.write(prompt + "\n")
                    log_file.write("GPT Markdown Output:\n")
                    log_file.write(markdown_text + "\n")
                    log_file.write("="*60 + "\n\n")
            return markdown_text
        except openai.RateLimitError as e:
            print(f"OpenAI rate limit error: {e}. Waiting 2 seconds before retrying ({attempt+1}/{max_retries})...")
            time.sleep(2)
        except Exception as e:
            # For other errors, raise immediately
            raise
    raise RuntimeError("Failed to convert OCR lines to markdown due to repeated rate limit errors.")

def process_vertices_list(vertices_list):
    """
    Process the vertices list to extract the bounding boxes of each line of text.
    """
    processed_vertices = []
    for line in vertices_list:
        processed_line = []
        for vertex in line:
            x = float(vertex.strip("()").split(",")[0])
            y = float(vertex.strip("()").split(",")[1])
            processed_line.append((x, y))
        processed_vertices.append(processed_line)
    return processed_vertices
            

def plot_vertices_list(image_path, vertices_list):
    """
    Plot the vertices list on the image.
    """
    image = cv2.imread(image_path)
    for line in vertices_list:
        for vertex in line:
            x = int(vertex[0])
            y = int(vertex[1])
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
    cv2.imshow("Vertices", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Save the image with vertices
    output_path = os.path.splitext(image_path)[0] + "_vertices.jpg"
    cv2.imwrite(output_path, image)
    print(f"Vertices image saved to {output_path}")
    return output_path

def preprocess_text(text, vertices_list):
    """
    Preprocess the text to remove unwanted strings
    and group lines of text.
    """
    processed_lines = []

    num_lines = len(text.split('\n'))
    num_vertices = len(vertices_list)

    print(f"Number of lines: {num_lines}")
    print(f"Number of vertices: {num_vertices}")

    # return processed_text

def save_ocr_dictionary(ocr_dict, output_path):
    """
    Save the OCR dictionary to a file.
    
    Args:
        ocr_dict (dict): The OCR dictionary to be saved.
        output_path (str): The path where the OCR dictionary will be saved.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(ocr_dict, f)

def load_ocr_dictionary(input_path):
    """
    Load the OCR dictionary from a file.
    
    Args:
        input_path (str): The path to the file containing the OCR dictionary.
    
    Returns:
        dict: The loaded OCR dictionary.
    """
    with open(input_path, 'rb') as f:
        ocr_dict = pickle.load(f)
    return ocr_dict

def process_ocr_dictionary_into_lines(lines, tolerance_percentage=0.05):
    """
    Groups lines by their y coordinate (with tolerance), then sorts each group by x coordinate.

    Args:
        lines (list): List of (text, topmost_y, leftmost_x) tuples or OCR dicts.
        tolerance_percentage (float): Tolerance for grouping by y.

    Returns:
        list: List of strings, each containing the text of a group of lines.
    """
    if not lines:
        return []

    # Convert dicts to (text, y, x) tuples if needed
    processed = []
    for item in lines:
        if isinstance(item, dict) and "vertices" in item and "text" in item:
            vertices = item["vertices"]
            # Ensure vertices are tuples of numbers
            topmost_y = min(float(v[1]) for v in vertices)
            leftmost_x = min(float(v[0]) for v in vertices)
            rightmost_x = max(float(v[0]) for v in vertices)
            processed.append((item["text"], topmost_y, leftmost_x, rightmost_x))
        elif isinstance(item, (list, tuple)) and len(item) == 3:
            # Already a tuple, but ensure y and x are numbers
            text, y, x = item
            processed.append((text, float(y), float(x)))
        else:
            continue

    if not processed:
        return []

    # Calculate tolerance in pixels
    all_y = [item[1] for item in processed]
    y_range = max(all_y) - min(all_y)
    tolerance = y_range * tolerance_percentage if y_range > 0 else 5

    # Sort lines by y
    processed = sorted(processed, key=lambda t: t[1])

    groups = []
    for item in processed:
        placed = False
        for group in groups:
            if abs(item[1] - group[0][1]) <= tolerance:
                group.append(item)
                placed = True
                break
        if not placed:
            groups.append([item])

    # Sort each group by x and join text with variable spaces
    result = []

    # Use the leftmost and rightmost x coordinates to determine the width of the text
    # Place words at their calculated positions in a fixed-width line
    for group in groups:
        group_sorted = sorted(group, key=lambda t: t[2])
        # Estimate average character width (in pixels)
        all_widths = [item[3] - item[2] for item in group_sorted if len(item) > 3 and len(item[0]) > 0]
        # avg_char_width = (sum(all_widths) / sum(len(item[0]) for item in group_sorted if len(item) > 3 and len(item[0]) > 0)) if all_widths else 8
        avg_char_width = 6

        # Determine the rightmost x to size the line
        max_right_x = max((item[3] if len(item) > 3 else item[2] + len(item[0]) * avg_char_width) for item in group_sorted)
        line_length = int(max_right_x // avg_char_width) + 10  # Add some buffer

        line_chars = [' '] * line_length

        for item in group_sorted:
            text = item[0]
            left_x = item[2]
            start_idx = int(round(left_x / avg_char_width))
            # Place the text at the calculated position
            for i, c in enumerate(text):
                idx = start_idx + i
                if idx < len(line_chars):
                    line_chars[idx] = c

        result.append(''.join(line_chars).rstrip())
    
    return result

def process_image_file(image_file, image_directory, markdown_directory, client):
    try:
        image_file_path = os.path.join(image_directory, image_file)
        markdown_file_name = os.path.splitext(image_file)[0] + ".md"
        markdown_file_path = os.path.join(markdown_directory, markdown_file_name)
        if os.path.exists(markdown_file_path):
            print(f"Markdown file {markdown_file_name} already exists. Skipping conversion.")
            return
        ocr_dict_file_path = os.path.join(markdown_directory, f"{os.path.splitext(image_file)[0]}_ocr.pkl")
        if os.path.exists(ocr_dict_file_path):
            print(f"OCR dictionary file {ocr_dict_file_path} already exists. Loading it...")
            ocr_dict = load_ocr_dictionary(ocr_dict_file_path)
        else:
            print(f"Extracting text from {image_file} using OCR...")
            ocr_dict = extract_text_with_google_vision(image_file_path)
            save_ocr_dictionary(ocr_dict, ocr_dict_file_path)
        ocr_lines = process_ocr_dictionary_into_lines(ocr_dict, tolerance_percentage=0.01)
        # lines_to_show = 5
        # print(f"Showing first {lines_to_show} lines of OCR text:")
        # for line in ocr_lines[:lines_to_show]:
        #     print(line)
        markdown_text = convert_ocr_lines_to_markdown(ocr_lines, client, log_dir=markdown_directory)
        print(f"Markdown text for {image_file} completed.")
        if markdown_text:
            print(f"Saving markdown text to {markdown_file_path}...")
            with open(markdown_file_path, 'w', encoding='utf-8') as markdown_file:
                markdown_file.write(markdown_text)
        return f"Processed {image_file}"
    except Exception as e:
        print(f"An error occurred processing {image_file}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error processing {image_file}: {e}"

def main():
    """
    Main function to run the script.
    """
    # Create a root window
    root = tk.Tk()

    # Read the OpenAI API key from the text file
    openai_key_file_path = os.path.join(os.getcwd(), "openai_key.txt")
    if os.path.exists(openai_key_file_path):
        with open(openai_key_file_path, 'r') as key_file:
            openai_api_key = key_file.read().strip()
    else:
        print("API key file not found. Please provide the API key manually.")
        openai_api_key = ""

    if openai_api_key == "":
        # Prompt the user to provide OpenAI API key using Tkinter
        openai_api_key = tk.simpledialog.askstring(
            "OpenAI API Key",
            "Enter your OpenAI API key:",
            initialvalue=openai_api_key
        )
        if not openai_api_key:
            print("No API key provided. Exiting.")
            root.destroy()
            exit(1)

    client = openai.OpenAI(api_key=openai_api_key)

    # Destroy the root window
    root.destroy()

    # Create a root window
    root = tk.Tk()

    # Using TKinter, prompt the user to provide Google Cloud API json key
    google_cloud_key_file_path = os.path.join(os.getcwd(), "google_cloud_key.json")
    if os.path.exists(google_cloud_key_file_path):
        with open(google_cloud_key_file_path, 'r') as key_file:
            google_cloud_api_key = key_file.read().strip()
    else:
        print("Google Cloud API key file not found. Please provide the API key manually.")
        google_cloud_api_key = ""

    if google_cloud_api_key == "":
        # Prompt the user to provide Google Cloud API key using Tkinter file dialog
        google_cloud_key_file_path = filedialog.askopenfilename(
            title="Select Google Cloud API Key File",
            filetypes=[("JSON files", "*.json")],
            initialdir=os.getcwd()
        )

    # Set the environment variable for Google Cloud API key
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_cloud_key_file_path

    # Destroy the root window
    root.destroy()

    # Create a root window
    root = tk.Tk()

    image_directory = None
    # image_directory = r"C:\Users\scleb\Documents\bimsc25\GitHub\PDF-Markdown-AI\250510_test_images"
    if image_directory is None:
        # Prompt the user for the file path of the image files
        image_directory = prompt_user_for_directory(root, "Select Directory with Image Files")
        if not image_directory:
            print("No directory selected. Exiting.")
            root.destroy()
            exit()

    markdown_directory = image_directory  # Save markdown files in the same directory as images

    # Destroy the root window
    root.destroy()

    # Get the list of image files in the directory
    image_files = [f for f in os.listdir(image_directory) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("No image files found in the selected directory.")

    # Sort the image files by the number in the filename
    image_numbers = {}
    for image_file in image_files:
        # Extract the number from the filename
        number = ''.join(filter(str.isdigit, image_file))
        if number:
            image_numbers[image_file] = int(number)
    image_files.sort(key=lambda x: image_numbers.get(x, float('inf')))
    # Print the sorted image files
    print("Sorted image files:")
    for image_file in image_files:
        print(image_file)

    # Create a root window
    root = tk.Tk()
    try:
        print("\n" * 20)
        # Use ThreadPoolExecutor to process images in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_image_file, image_file, image_directory, markdown_directory, client)
                       for image_file in image_files]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                print(result)
        print("All images converted to markdown successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    # Close the root window
    root.destroy()

if __name__ == "__main__":
    main()

