# This is a streamlit app that allows the user to input a directory path
# Then the app will list all folders in that directory
# For each folder, it will validate that a pickle file and a markdown file exist for each image in the folder
# The files will be named the same as the image but with .pkl and .md extensions respectively

import streamlit as st
import os
import time
import plotly.graph_objects as go

def is_image_file(filename):
    return filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'))

def validate_folder(folder_path):
    results = []
    for fname in os.listdir(folder_path):
        if is_image_file(fname):
            base, _ = os.path.splitext(fname)
            pkl_path = os.path.join(folder_path, base + '_ocr.pkl')
            md_path = os.path.join(folder_path, base + '.md')
            pkl_exists = os.path.exists(pkl_path)
            md_exists = os.path.exists(md_path)
            results.append({
                'image': fname,
                'pkl': pkl_exists,
                'md': md_exists
            })
    return results

st.title('Folder Image Validator')
# Add refresh timer
refresh_interval = st.number_input('Refresh interval (milliseconds):', min_value=0, max_value=60000, value=int(1000 / 8), step=1000)
if refresh_interval > 0:
    st.write(f"Refreshing every {refresh_interval} milliseconds...")
    time.sleep(refresh_interval / 1000.0)  # Convert milliseconds to seconds

dir_path = st.text_input('Enter directory path:', value='')

if dir_path and os.path.isdir(dir_path):
    folders = [f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))]
    # Sort folders by the integer before the first underscore
    def folder_sort_key(folder):
        parts = folder.split('_', 1)
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return float('inf')  # Non-integer folders go last
    folders.sort(key=folder_sort_key)
    st.write(f"Found {len(folders)} folders:")
    # Display folders in a grid with rows of columns
    num_cols = 5
    for row_start in range(0, len(folders), num_cols):
        cols = st.columns(num_cols)
        for col_idx, folder in enumerate(folders[row_start:row_start+num_cols]):
            with cols[col_idx]:
                st.markdown(f"**Folder: {folder}**")
                folder_path = os.path.join(dir_path, folder)
                validation = validate_folder(folder_path)
                total = len(validation)
                if total == 0:
                    st.write('No images found.')
                else:
                    valid = sum(1 for item in validation if item['pkl'] and item['md'])
                    percent = (valid / total) * 100
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = percent,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Validation %"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#00cc96"},
                        },
                    ))
                    fig.update_layout(width=220, height=180, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=False, key=f"gauge_{folder}")
                    st.write(f"{valid} of {total} images valid ({percent:.1f}%)")
                    with st.expander("Details"):
                        not_validated = [item for item in validation if not (item['pkl'] and item['md'])]
                        if not_validated:
                            st.write('Files not validated:')
                            for item in not_validated:
                                missing = []
                                if not item['pkl']:
                                    missing.append('.pkl')
                                if not item['md']:
                                    missing.append('.md')
                                st.write(f"- {item['image']} (missing: {', '.join(missing)})")
else:
    st.info('Please enter a valid directory path.')

