import os

# Specify the directory path
directory = "extracted_images/ALES/"

# Specify the output file
output_file = "new.txt"

# Function to extract numeric part from the filename
def extract_number(filename):
    return int(''.join(filter(str.isdigit, filename)))

# Open the file for writing
with open(output_file, 'w') as f:
    # Iterate through the folders and files in the directory
    for folder_name, subfolders, filenames in os.walk(directory):
        # Filter out only .png files
        png_files = [filename for filename in filenames if filename.endswith('.png')]
        
        if png_files:
            # Sort the .png files based on the numeric part of the file name
            png_files.sort(key=extract_number)
            
            # Write the folder name
            f.write(f"Folder: {folder_name}\n")
            
            # Write the first .png file
            first_file_path = os.path.join(folder_name, png_files[0])
            f.write(f"    First File: {first_file_path}\n")
            
            # Write the last .png file
            if len(png_files) > 1:
                last_file_path = os.path.join(folder_name, png_files[-1])
                f.write(f"    Last File: {last_file_path}\n")
            f.write("\n")  # Add a newline for clarity between folders

print(f"First and last .png file paths have been saved to {output_file}")
