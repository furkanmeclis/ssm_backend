import os
import yaml
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Load the sections.yaml file
def load_sections_data():
    with open('sections.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# Define the directory where images are stored
base_dir = 'extracted_images/'

# Function to count images in a directory and return file names
def list_images_in_directory(path):
    try:
        return sorted([f for f in os.listdir(path) if f.endswith('.png')])
    except FileNotFoundError:
        return []

# Function to check for mismatches
def check_for_mismatches():
    sections_data = load_sections_data()
    mismatches = []
    for exam_name, years in sections_data.items():
        for year, data in years.items():
            year_str = str(year)  # Convert year to string
            for section, expected_count in data['sections'].items():
                section_dir = os.path.join(base_dir, exam_name, year_str, section)
                actual_images = list_images_in_directory(section_dir)
                actual_count = len(actual_images)
                if actual_count != expected_count:
                    mismatches.append({
                        'exam': exam_name,
                        'year': year_str,
                        'section': section,
                        'actual': actual_count,
                        'expected': expected_count,
                        'missing': expected_count - actual_count,  # Calculate missing images
                        'actual_images': actual_images,
                        'section_dir': section_dir
                    })
    return mismatches

# Function to display the mismatches in a tkinter table with grouping
def display_mismatches(mismatches, tree):
    # Clear the Treeview
    for item in tree.get_children():
        tree.delete(item)

    # Group mismatches by exam and year
    exams_group = {}
    for mismatch in mismatches:
        exam = mismatch['exam']
        year = mismatch['year']

        if exam not in exams_group:
            exams_group[exam] = {}

        if year not in exams_group[exam]:
            exams_group[exam][year] = []

        exams_group[exam][year].append(mismatch)

    # Insert the grouped data into the Treeview
    for exam, years in exams_group.items():
        exam_node = tree.insert('', 'end', text=exam, open=True)  # Create a parent node for each exam
        for year, sections in years.items():
            year_node = tree.insert(exam_node, 'end', text=f'Year: {year}', open=True)  # Add child nodes for each year
            for section in sections:
                missing_count = section['missing']
                tag = 'red' if missing_count > 0 else ''
                tree.insert(year_node, 'end', values=(section['section'], section['actual'], section['expected'], missing_count), tags=(tag,), iid=f"{exam}_{year}_{section['section']}")  # Add section as children of the year node

# Function to handle click event and show missing files
def on_row_click(event, tree, mismatches):
    item = tree.selection()[0]
    item_values = tree.item(item, 'values')
    section_name = item_values[0]

    # Find the mismatch data for the clicked row
    for mismatch in mismatches:
        if mismatch['section'] == section_name:
            # Compare the actual images with expected range
            actual_images = mismatch['actual_images']
            section_dir = mismatch['section_dir']
            expected_count = mismatch['expected']
            missing_files = []

            # Check for missing files by comparing numbers (assuming files are named 1.png, 2.png, ..., etc.)
            expected_files = [f"{i}.png" for i in range(1, expected_count + 1)]
            missing_files = [f for f in expected_files if f not in actual_images]

            # Show missing files in a message box
            if missing_files:
                missing_str = "\n".join(missing_files)
                messagebox.showinfo("Missing Files", f"Missing files for section {section_name}:\n{missing_str}")
            else:
                messagebox.showinfo("No Missing Files", f"All expected files are present in section {section_name}.")

            break

# Function to refresh the mismatches
def refresh_mismatches(tree):
    mismatches = check_for_mismatches()
    display_mismatches(mismatches, tree)
    return mismatches

# Main function to create the GUI
def create_gui():
    root = tk.Tk()
    root.title("Image Mismatches")
    root.geometry("1100x1000")  # Set window size

    # Create the Treeview widget
    tree = ttk.Treeview(root, columns=('Section', 'Actual', 'Expected', 'Missing'), show='tree headings')

    # Define the column headings
    tree.heading('Section', text='Section')
    tree.heading('Actual', text='Actual Images')
    tree.heading('Expected', text='Expected Images')
    tree.heading('Missing', text='Missing Images')

    # Define column widths
    tree.column('Section', width=300)
    tree.column('Actual', width=100)
    tree.column('Expected', width=100)
    tree.column('Missing', width=100)

    # Add the Treeview to the window
    tree.pack(expand=True, fill='both')

    # Initial load of mismatches
    mismatches = refresh_mismatches(tree)

    # Bind the row click event to display missing files
    tree.bind("<Double-1>", lambda event: on_row_click(event, tree, mismatches))

    # Create the Refresh button
    refresh_button = ttk.Button(root, text="Refresh", command=lambda: refresh_mismatches(tree))
    refresh_button.pack(side=tk.BOTTOM, pady=10)

    # Start the tkinter main loop
    root.mainloop()

# Run the GUI
create_gui()
