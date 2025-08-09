import os
import yaml

# Set the root directory
root_dir = "../EXAM_PDFS"

# Dictionary to hold the file structure
file_structure = {}

# Default start text, you can modify this based on your requirement
default_start_text = "Bu testte"

# Walk through the directory
for root, dirs, files in os.walk(root_dir):
    relative_path = os.path.relpath(root, root_dir)
    parts = relative_path.split(os.sep)
    
    # Navigate through the dictionary structure
    current_level = file_structure
    for part in parts:
        if part not in current_level:
            current_level[part] = {}
        current_level = current_level[part]
    
    # Add files to the current level
    for file in files:
        current_level[file] = {
            "start_text": default_start_text,
            "sections": None
        }

# Write the file structure to a YAML file
with open("config.yaml", "w") as config_file:
    yaml.dump(file_structure, config_file, default_flow_style=False, allow_unicode=True)

print("config.yaml file created successfully!")
