# This script sorts images and PDFs in a folder based on a csv file with sections, start and end pages.
# Streamlit is used for the GUI.

import streamlit as st
import pandas as pd
import os
import shutil

st.set_page_config(
    page_title="PDF Image Sorter",
    page_icon=":page_facing_up:",
    layout="wide"
)

st.title("PDF Image Sorter")
st.write("This app sorts images and PDFs in a folder based on a CSV file with sections, start and end pages.")
st.write("Upload a CSV file with the following columns: 'section title', 'start page', 'end page'.")

# File uploader for CSV
csv_file = st.file_uploader("Upload CSV file", type=["csv"])

if csv_file is not None:
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Display the dataframe
    st.write("Data from CSV:")
    st.dataframe(df)

    # Display the current working directory
    st.write("Current working directory:", os.getcwd())

    # Allow user to select a directory to find the files
    st.write("Please ensure that the files are named as 'page_1.pdf', 'page_2.pdf', etc. and 'page_1.jpg', 'page_2.jpg', etc.")
    
    # Input to specify the directory containing the files
    directory = st.text_input("Enter the directory containing the files (leave empty for current directory):", value=os.getcwd())

    # Get all files in the specified directory
    if directory:
        all_files = os.listdir(directory)
    else:
        all_files = os.listdir(os.getcwd())

    # Display the filenames in the directory
    st.write("Files in the directory:")
    print(f'type(all_files) {type(all_files)}')
    filenames = [f for f in all_files if f.endswith('.pdf') or f.endswith('.jpg')]
    with st.expander("Show Filenames"):
        st.write(str(filenames))

    # Input for file number vs page number offset
    page_offset = st.number_input("Enter the page number offset (default is 0):", min_value=0, value=0, step=1)
    if page_offset != 0:
        st.warning(f"Note: The page numbers in the CSV will be adjusted by {page_offset}.")
    # Adjust the start and end pages in the dataframe
    if 'start page' in df.columns:
        df['start page'] = df['start page'] + page_offset

    if 'end page' in df.columns:
        df['end page'] = df['end page'] + page_offset

    # Display the adjusted dataframe if page offset is applied
    if page_offset != 0:
        st.write("Adjusted Data from CSV:")
        st.dataframe(df)

    # Check if required columns are present
    if 'section title' in df.columns and 'start page' in df.columns and 'end page' in df.columns:
        st.success("CSV file is valid.")
        
        # Add a button to start processing
        if st.button("Start Sorting"):
            # Process each section
            for index, row in df.iterrows():
                
                # Create a section folder
                section_title = row['section title']
                start_page = row['start page']
                end_page = row['end page']

                section_folder_name = str(index + 1) + "_" + section_title.replace(" ", "_")

                section_folder = os.path.join("sorted_files", section_folder_name)
                if not os.path.exists(section_folder):
                    os.makedirs(section_folder)

                st.write(f"Processing section: {section_title} (Pages {start_page} to {end_page})")

                # Files are named page_1.pdf, page_2.pdf, etc.
                for page_num in range(start_page, end_page + 1):
                    pdf_file_name = f"page_{page_num}.pdf"
                    jpg_file_name = f"page_{page_num}.jpg"

                    src_pdf = os.path.join(directory, pdf_file_name)
                    src_jpg = os.path.join(directory, jpg_file_name)
                    dst_pdf = os.path.join(section_folder, pdf_file_name)
                    dst_jpg = os.path.join(section_folder, jpg_file_name)

                    if pdf_file_name in all_files:
                        if os.path.exists(src_pdf):
                            shutil.copy2(src_pdf, dst_pdf)
                            st.write(f"Copied {pdf_file_name} to {section_folder}")
                        else:
                            st.warning(f"File not found: {src_pdf}")
                    if jpg_file_name in all_files:
                        if os.path.exists(src_jpg):
                            shutil.copy2(src_jpg, dst_jpg)
                            st.write(f"Copied {jpg_file_name} to {section_folder}")
                        else:
                            st.warning(f"File not found: {src_jpg}")
