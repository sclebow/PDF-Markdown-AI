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

def convert_to_markdown(image_file_path, client):
    """
    Converts a image file to markdown format using OpenAI's GPT model.
    """
    # Read the image file
    with open(image_file_path, 'rb') as f:
        image_data = f.read()

    # Encode the image data to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')

    message_1_text = """
Convert this image into markdown, including any tables.
Transcribe the table exactly as shown in the image. Do not guess, infer, or fill in missing data.
If a cell is blank, unclear, or contains a symbol (like a dash or arrow), reproduce it exactly as shown.
Some of the data in the image may be misaligned; please carefully match each value to its correct column, and pay special attention to blank entries.
Do not invent, hallucinate, or use any information that is not visible in the image. Only use data that is clearly visible in the image.
If you are unsure about a value, leave the cell blank or write 'unclear'.
Provide the markdown text only, without any additional text or formatting.
Do not include any code blocks or HTML tags."""
    
    message_2_text = """
Carefully verify that every value in the markdown table matches the image exactly.
If any value is unclear, leave the cell blank or mark as 'unclear'. Do not guess, infer, or fill in missing data.
Do not add, remove, or change any values from what is visible in the image. Do not use any information that is not visible in the image.
Please provide the markdown text only, without any additional text or formatting.
Please do not include any code blocks or HTML tags.
"""
    
    sent_timestamp = datetime.datetime.now().isoformat()

    # Use OpenAI's GPT model to convert the image to markdown
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": message_1_text }
                ],
            },
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": message_2_text },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

#     # Ask ChatGPT to verify the markdown by sending the markdown text back to it and asking it to check for errors

#     message_3_text = """
# Please verify the markdown text below for any errors or inaccuracies.
# If you find any errors, please correct them.
# If the markdown text is correct, please confirm that it is accurate.
# Do not add, remove, or change any values from what is visible in the image. Do not use any information that is not visible in the image.
# Please provide the markdown text only, without any additional text or formatting.
# Do not include any code blocks or HTML tags.
# """
#     response = client.responses.create(
#         model="gpt-4.1",
#         input=[
#             {
#                 "role": "user",
#                 "content": [
#                     { "type": "input_text", "text": message_3_text },
#                     { "type": "input_text", "text": response.output_text },
#                     {
#                         "type": "input_image",
#                         "image_url": f"data:image/jpeg;base64,{base64_image}",
#                     },
#                 ],
#             }
#         ],
#     )
    # Print the response from OpenAI
    print("Response from OpenAI:")
    print(response.output_text)

    response_timestamp = datetime.datetime.now().isoformat()
    time_taken = (datetime.datetime.fromisoformat(response_timestamp) - datetime.datetime.fromisoformat(sent_timestamp)).total_seconds()
    print(f"Time taken for conversion: {time_taken} seconds")

    # Save the full response, messages, and timestamp to a log file
    log_file_path = os.path.join(os.path.dirname(image_file_path), "conversion_log.txt")
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Sent Timestamp: {sent_timestamp}\n")
        log_file.write(f"Image: {image_file_path}\n")
        log_file.write(f"Message 1: {message_1_text.strip()}\n")
        log_file.write(f"Message 2: {message_2_text.strip()}\n")
        log_file.write(f"Response: {response}\n")
        log_file.write(f"Response Timestamp: {response_timestamp}\n")
        log_file.write(f"Time Taken: {time_taken} seconds\n")
        log_file.write("\n" + "="*50 + "\n\n")
       
    markdown_text = response.output_text

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
    key_file_path = os.path.join(os.path.dirname(__file__), "openai_key.txt")
    if os.path.exists(key_file_path):
        with open(key_file_path, 'r') as key_file:
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

    # Prompt the user for the file path of the image files
    image_directory = prompt_user_for_directory(root, "Select Directory with Image Files")
    if not image_directory:
        return

    # Prompt the user for the directory to save the markdown files
    markdown_directory = prompt_user_for_directory(root, "Select Directory to Save Markdown Files")
    if not markdown_directory:
        return

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
        
        # Convert the image to markdown
        markdown_text = convert_to_markdown(image_file_path, client)
        
        # Save the markdown text to a file
        save_markdown(markdown_text, markdown_file_path)
        
        print(f"Converted {image_file} to {markdown_file_name}")

    # Print a message indicating that the process is complete
    print("All images converted to markdown successfully.")
    # Close the root window
    root.destroy()

if __name__ == "__main__":
    main()