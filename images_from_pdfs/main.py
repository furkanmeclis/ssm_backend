import os
from pdf2image import convert_from_path
import pandas as pd
import yaml
import re
from unidecode import unidecode
import logging

# Paths
base_dir = "images"
output_dir = "extracted_images"
excel_dir = "excel_tables"

# Create output directory if not exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load sections data from 'sections.yaml'
with open('sections.yaml', 'r', encoding='utf-8') as f:
    sections_data = yaml.safe_load(f)

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup a logger; clears pre-existing logs."""
    handler = logging.FileHandler(log_file, mode='w')  # 'w' mode clears the file
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

    return logger

# Setup loggers
conversion_logger = setup_logger('conversion_logger', 'conversion_log.txt')
process_logger = setup_logger('process_logger', 'process_log.txt')

def read_question_mapping(exam_type, year):
    """Reads and filters the Excel data for the given exam type and year."""
    excel_file = os.path.join(excel_dir, f"{exam_type}.xlsx")
    if not os.path.exists(excel_file):
        process_logger.error(f"Excel file not found: {excel_file}")
        return None
    df = pd.read_excel(excel_file)
    # Filter the dataframe for the specific year and exam type
    df_filtered = df[(df['SINAV ADI'] == exam_type) & (df['SINAV YILI'] == int(year))]
    if df_filtered.empty:
        process_logger.warning(f"No data found for {exam_type} {year} in {excel_file}")
        return None
    return df_filtered[['SORU NUMARASI', 'DERS ADI']]

def normalize_string(s):
    """Helper function to normalize strings by removing spaces, special characters, and converting to ASCII."""
    return unidecode(re.sub(r'\s+', '', s.lower()))

def find_folder_recursively(base_path, folder_name):
    """Recursively searches for a folder matching the given name."""
    normalized_folder_name = normalize_string(folder_name)
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            normalized_d = normalize_string(d)
            if normalized_d == normalized_folder_name:
                return os.path.join(root, d)
    # Folder not found
    return None

def find_file_case_insensitive(path, extension):
    """Finds a file with the given extension in the specified directory."""
    extension_lower = extension.lower()
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)) and item.lower().endswith(extension_lower):
            return os.path.join(path, item)
    return None

def convert_pdf_to_images(pdf_path, output_folder, page_number, image_filename):
    """Converts a specific page of a PDF into a PNG image and saves it to the output folder."""
    
    # Check if the PDF file exists
    if not os.path.exists(pdf_path):
        conversion_logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    try:
        # Convert the specific page from the PDF
        images = convert_from_path(pdf_path, dpi=300, first_page=page_number, last_page=page_number)
        if images:
            page = images[0]  # First (and only) image since we are converting a single page
            image_output_path = os.path.join(output_folder, image_filename)
            
            # Save the image as PNG
            page.save(image_output_path, "PNG")
            return True
        else:
            conversion_logger.warning(f"No images extracted from {pdf_path} for page {page_number}")
            return False
    
    except Exception as e:
        conversion_logger.error(f"Error converting {pdf_path} (page {page_number}): {e}")
        return False

def adjust_subject_section_mapping(exam_type_upper, year, sections, current_subject_section_mapping):
    """
    Adjusts the subject to section mappings dynamically based on exam type and year.
    This function allows for flexibility in handling different folder structures across years and exams.
    """
    # Define special mappings here
    # Format: exam_type_upper -> {year: {subject: new_section, ...}, ...}
    special_mappings = {
        'LYS': {
            2017: {
                'Matematik': 'sayisal-testi',
                'Geometri': 'sayisal-testi',
            }
        }
        # Add other exam types if needed
    }
    # Check if there are special mappings for the given exam type and year
    if exam_type_upper in special_mappings:
        if year in special_mappings[exam_type_upper]:
            mappings = special_mappings[exam_type_upper][year]
            for subject, new_section in mappings.items():
                original_section = current_subject_section_mapping.get(subject)
                current_subject_section_mapping[subject] = new_section
                process_logger.info(f"{exam_type_upper} {year}: Mapped '{subject}' from '{original_section}' to '{new_section}'")

    # Add more logic here such as checking for the existence of 'sayisal-testi'

    return current_subject_section_mapping

def process_exam(exam_type):
    exam_type_upper = exam_type.upper()
    if exam_type_upper == 'ALES':
        process_ales_exam(exam_type_upper)
        return  # Skip the rest as ALES is handled separately
    
    for year in sections_data.get(exam_type_upper, {}):
        process_logger.info(f"Processing {exam_type_upper} {year}")
        try:
            sections = sections_data[exam_type_upper][year]['sections']
        except KeyError:
            process_logger.error(f"Sections data not found for {exam_type_upper} {year}")
            continue

        mapping_df = read_question_mapping(exam_type_upper, year)
        if mapping_df is None:
            continue

        # Initialize subject page counters
        subject_page_counters = {}

        # Get the subject-section mapping for the current exam type
        current_subject_section_mapping = subject_section_mapping.get(exam_type_upper, {}).copy()

        # Adjust mappings dynamically based on exam type and year
        current_subject_section_mapping = adjust_subject_section_mapping(
            exam_type_upper,
            year,
            sections,
            current_subject_section_mapping
        )

        # Process each question in the mapping_df
        for idx in range(len(mapping_df)):
            question_row = mapping_df.iloc[idx]
            subject = question_row['DERS ADI']
            question_number = question_row['SORU NUMARASI']

            # Determine the section name based on subject
            section_name = current_subject_section_mapping.get(subject)
            if not section_name:
                process_logger.error(f"Could not determine section for subject '{subject}' in {exam_type_upper} {year}")
                continue

            # Proceed with the rest of the code
            base_path = os.path.join(base_dir, exam_type_upper, str(year))
            subject_folder = get_subject_folder(base_path, subject, exam_type_upper)
            if not subject_folder:
                process_logger.error(f"Subject folder not found for {subject} in {base_path}")
                continue

            # Find the PDF in the subject_folder
            pdf_file = find_file_case_insensitive(subject_folder, '.pdf')
            if not pdf_file:
                process_logger.error(f"No PDF files found in {subject_folder}")
                continue

            # Update page counter for the subject
            subject_normalized = normalize_string(subject)
            if subject_normalized not in subject_page_counters:
                subject_page_counters[subject_normalized] = 1
            else:
                subject_page_counters[subject_normalized] += 1
            
            subjects = check_if_mulptiple_subjects_in_one_pdf(base_path, exam_type_upper, year, subject_folder, subject)

            if subjects:
                # Ensure that each subject has an initialized page counter before proceeding
                for s in subjects:
                    subject_normalized_temp = normalize_string(s)
                    if subject_normalized_temp not in subject_page_counters:
                        subject_page_counters[subject_normalized_temp] = 0

                # Normalize subject names for comparison
                subject_normalized = normalize_string(subject)

                # Calculate the total number of pages of all preceding subjects
                preceding_pages_count = sum(subject_page_counters[normalize_string(s)] for s in subjects if normalize_string(s) != subject_normalized)

                # Add preceding pages to the current subject's page counter to get the current page number
                page_number = preceding_pages_count + subject_page_counters[subject_normalized]
            else:
                # If no multiple subjects, just use the current page counter for the subject
                page_number = subject_page_counters[subject_normalized]

            section_output_dir = os.path.join(output_dir, exam_type_upper, str(year), section_name)
            if not os.path.exists(section_output_dir):
                os.makedirs(section_output_dir)

            # Extract the page corresponding to the local page number
            image_filename = f"{question_number}.png"
            image_output_path = os.path.join(section_output_dir, image_filename)
            if os.path.exists(image_output_path):
                continue

            success = convert_pdf_to_images(pdf_file, section_output_dir, page_number, image_filename)
            if not success:
                process_logger.error(f"Failed to convert PDF {pdf_file} for {subject}")

        process_logger.info(f"Finished processing {exam_type_upper} {year}")

def check_if_mulptiple_subjects_in_one_pdf(base_path, exam_type_upper, year, subject_folder, subject):
    """
    Checks if there are multiple subjects in the same PDF by using the subject_folder_mapping.
    If multiple subjects share the same folder, returns a list of these subjects, otherwise returns False.
    """
    # First, find the current mapping for the given exam type
    current_mapping = subject_folder_mapping.get(exam_type_upper, {})

    # Find out if multiple subjects map to the same folder as the given subject
    current_subject_folder = current_mapping.get(subject)
    if not current_subject_folder:
        process_logger.error(f"Mapping for subject '{subject}' not found in exam type '{exam_type_upper}'")
        return False

    # Get other subjects sharing the same folder
    multiple_subjects = [sub for sub, folder in current_mapping.items() if folder == current_subject_folder]

    # If more than one subject shares the same folder, return the list of subjects
    if len(multiple_subjects) > 1:
        return multiple_subjects
    else:
        return False

def process_ales_exam(exam_type_upper):
    """Special processing for ALES exams due to their unique structure."""
    for year in sections_data.get(exam_type_upper, {}):
        process_logger.info(f"Processing {exam_type_upper} {year}")
        mapping_df = read_question_mapping(exam_type_upper, year)
        if mapping_df is None:
            continue

        # Identify ALES exams (e.g., ALES-1, ALES 1)
        base_path = os.path.join(base_dir, exam_type_upper, str(year))
        if not os.path.exists(base_path):
            process_logger.error(f"Base path not found: {base_path}")
            continue

        ales_exams = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

        # Sort ALES exams to process them in order
        def extract_exam_number(name):
            match = re.search(r'(\d+)', name)
            return int(match.group()) if match else 0

        ales_exams_sorted = sorted(ales_exams, key=extract_exam_number)

        # Initialize question number counter
        question_number_counter = 1

        for ales_exam in ales_exams_sorted:
            ales_exam_path = os.path.join(base_path, ales_exam)
            process_logger.info(f"Processing {ales_exam} in {year}")

            # Check if SAYISAL and SÖZEL folders exist
            subfolders = [d for d in os.listdir(ales_exam_path) if os.path.isdir(os.path.join(ales_exam_path, d))]
            normalized_subfolders = [normalize_string(d) for d in subfolders]

            has_sayisal_sozel = any(s in normalized_subfolders for s in ['sayisal1', 'sayisal2', 'sozel1', 'sozel2', 'sayisal', 'sozel'])

            if has_sayisal_sozel:
                # Process with SAYISAL/SÖZEL structure
                process_logger.info(f"Using SAYISAL/SÖZEL structure for {ales_exam} in {year}")
                question_number_counter = process_ales_with_sayisal_sozel(ales_exam, ales_exam_path, year, question_number_counter, mapping_df)
            else:
                # Process subjects directly under the ALES exam folder
                process_logger.info(f"Subjects are directly under {ales_exam} in {year}")
                question_number_counter = process_ales_without_sayisal_sozel(ales_exam, ales_exam_path, year, question_number_counter, mapping_df)

            process_logger.info(f"Finished processing {ales_exam} in {year}")

        process_logger.info(f"Finished processing {exam_type_upper} {year}")

def process_ales_with_sayisal_sozel(ales_exam, ales_exam_path, year, question_number_counter, mapping_df):
    """Processes ALES exams with SAYISAL/SÖZEL folders."""
    # Build the output directory
    base_output_dir = os.path.join(output_dir, 'ALES', str(year))

    mapping_df_indexed = mapping_df.set_index('SORU NUMARASI', drop=False)

    # Sections within each ALES exam
    sections_in_ales = ['SAYISAL1', 'SAYISAL2', 'SÖZEL1', 'SÖZEL2', 'SAYISAL', 'SÖZEL']
    for section_code in sections_in_ales:
        # Use the find_section_folder function
        section_folder = find_section_folder(ales_exam_path, section_code)
        if not section_folder:
            process_logger.warning(f"Section {section_code} not found in {ales_exam_path}")
            continue

        # Extract exam number
        exam_number_match = re.search(r'(\d+)', ales_exam)
        exam_number = exam_number_match.group() if exam_number_match else 'unknown'

        # Normalize and construct the output section name
        section_name_normalized = unidecode(section_code.lower())
        section_name_with_hyphen = re.sub(r'([a-zA-Z]+)(\d+)', r'\1-\2', section_name_normalized)
        output_section_name = f"ales-{exam_number}-{section_name_with_hyphen}-testi"

        section_output_dir = os.path.join(base_output_dir, output_section_name)
        if not os.path.exists(section_output_dir):
            os.makedirs(section_output_dir)

        # Get the subjects within the section
        subjects = os.listdir(section_folder)
        for subject in subjects:
            subject_folder = os.path.join(section_folder, subject)
            if not os.path.isdir(subject_folder):
                continue

            # Find the PDF in the subject folder
            pdf_file = find_file_case_insensitive(subject_folder, '.pdf')
            if not pdf_file:
                process_logger.error(f"No PDF files found in {subject_folder}")
                continue

            # Read the PDF to get the number of pages
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_file)
                num_pages = len(reader.pages)
            except Exception as e:
                process_logger.error(f"Error reading PDF {pdf_file}: {e}")
                continue

            # For each page in the PDF, extract the image
            for local_page_number in range(1, num_pages + 1):
                if question_number_counter not in mapping_df_indexed.index:
                    process_logger.error(f"Question number {question_number_counter} not found in mapping_df")
                    question_number_counter += 1
                    continue

                question_row = mapping_df_indexed.loc[question_number_counter]

                image_filename = f"{question_number_counter}.png"
                image_output_path = os.path.join(section_output_dir, image_filename)
                if os.path.exists(image_output_path):
                    question_number_counter += 1
                    continue

                success = convert_pdf_to_images(pdf_file, section_output_dir, local_page_number, image_filename)
                if not success:
                    process_logger.error(f"Failed to convert PDF {pdf_file} for {subject} on page {local_page_number}")
                else:
                    conversion_logger.info(f"Processed question {question_number_counter} for {subject}")
                question_number_counter += 1

    return question_number_counter

def process_ales_without_sayisal_sozel(ales_exam, ales_exam_path, year, question_number_counter, mapping_df):
    """Processes ALES exams without SAYISAL/SÖZEL folders."""
    # Build the output directory
    base_output_dir = os.path.join(output_dir, 'ALES', str(year))

    # Create a copy of mapping_df with 'SORU NUMARASI' as the index
    mapping_df_indexed = mapping_df.set_index('SORU NUMARASI', drop=False)

    # Extract exam number
    exam_number_match = re.search(r'(\d+)', ales_exam)
    exam_number = exam_number_match.group() if exam_number_match else 'unknown'

    subjects = os.listdir(ales_exam_path)
    for subject in subjects:
        subject_folder = os.path.join(ales_exam_path, subject)
        if not os.path.isdir(subject_folder):
            continue

        # Find the PDF in the subject folder
        pdf_file = find_file_case_insensitive(subject_folder, '.pdf')
        if not pdf_file:
            process_logger.error(f"No PDF files found in {subject_folder}")
            continue

        # Read the PDF to get the number of pages
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)
        except Exception as e:
            process_logger.error(f"Error reading PDF {pdf_file}: {e}")
            continue

        # Determine the section based on the subject
        subject_normalized = normalize_string(subject)

        if subject_normalized in ['matematik', 'geometri']:
            section_name = f"ales-{exam_number}-sayisal-1-testi"
        elif subject_normalized == 'turkce':
            section_name = f"ales-{exam_number}-sozel-1-testi"
        else:
            section_name = f"ales-{exam_number}-genel-testi"

        section_output_dir = os.path.join(base_output_dir, section_name)
        if not os.path.exists(section_output_dir):
            os.makedirs(section_output_dir)

        # For each page in the PDF, extract the image
        for local_page_number in range(1, num_pages + 1):
            if question_number_counter not in mapping_df_indexed.index:
                process_logger.error(f"Question number {question_number_counter} not found in mapping_df")
                question_number_counter += 1
                continue

            question_row = mapping_df_indexed.loc[question_number_counter]

            image_filename = f"{question_number_counter}.png"
            image_output_path = os.path.join(section_output_dir, image_filename)
            if os.path.exists(image_output_path):
                question_number_counter += 1
                continue

            success = convert_pdf_to_images(pdf_file, section_output_dir, local_page_number, image_filename)
            if not success:
                process_logger.error(f"Failed to convert PDF {pdf_file} for {subject} on page {local_page_number}")
            else:
                conversion_logger.info(f"Processed question {question_number_counter} for {subject}")
            question_number_counter += 1

    return question_number_counter

def find_ales_exam_folder(base_path, exam_number):
    """Finds the ALES exam folder matching the given exam number."""
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            # Normalize folder name to compare
            normalized_folder_name = normalize_string(folder_name)
            if re.search(r'\bales[\s-]*{}$'.format(exam_number), normalized_folder_name):
                return folder_path
    return None

def process_ales_section(section_name_full, year, start_question_number, end_question_number, mapping_df):
    """Processes a specific section of an ALES exam."""

    # Extract exam number and section code from section_name_full
    match = re.match(r'ales-(\d+)-([a-zA-Z]+-\d+)-testi', section_name_full)
    if match:
        exam_number = match.group(1)
        section_code = match.group(2).replace('-', '').upper()  # E.g., 'sayisal-1' -> 'SAYISAL1'
    else:
        process_logger.error(f"Invalid section name format: {section_name_full}")
        return start_question_number

    # Build the paths to the exam and section folders
    base_path = os.path.join(base_dir, 'ALES', str(year))
    ales_exam_folder = find_ales_exam_folder(base_path, exam_number)
    if not ales_exam_folder:
        process_logger.error(f"ALES exam folder not found for exam number {exam_number} in {base_path}")
        return start_question_number

    # Use the find_section_folder function
    section_folder = find_section_folder(ales_exam_folder, section_code)
    if not section_folder:
        process_logger.warning(f"Section {section_code} not found in {ales_exam_folder}")
        return start_question_number

    # Build the output directory
    section_output_dir = os.path.join(output_dir, 'ALES', str(year), section_name_full)
    if not os.path.exists(section_output_dir):
        os.makedirs(section_output_dir)

    # Create a copy of mapping_df with 'SORU NUMARASI' as the index
    mapping_df_indexed = mapping_df.set_index('SORU NUMARASI', drop=False)

    question_number_counter = start_question_number

    # Get the subjects within the section
    subjects = os.listdir(section_folder)
    for subject in subjects:
        subject_folder = os.path.join(section_folder, subject)
        if not os.path.isdir(subject_folder):
            continue

        # Find the PDF in the subject folder
        pdf_file = find_file_case_insensitive(subject_folder, '.pdf')
        if not pdf_file:
            process_logger.error(f"No PDF files found in {subject_folder}")
            continue

        # Read the PDF to get the number of pages
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)
        except Exception as e:
            process_logger.error(f"Error reading PDF {pdf_file}: {e}")
            continue

        # For each page in the PDF, extract the image
        for local_page_number in range(1, num_pages + 1):
            global_question_number = start_question_number + (local_page_number - 1)

            if global_question_number > end_question_number:
                break  # Reached the number of questions for this section

            if global_question_number not in mapping_df_indexed.index:
                process_logger.error(f"Question number {global_question_number} not found in mapping_df")
                continue

            question_row = mapping_df_indexed.loc[global_question_number]

            image_filename = f"{global_question_number}.png"
            image_output_path = os.path.join(section_output_dir, image_filename)
            if os.path.exists(image_output_path):
                continue

            success = convert_pdf_to_images(pdf_file, section_output_dir, local_page_number, image_filename)
            if not success:
                process_logger.error(f"Failed to convert PDF {pdf_file} for {subject} on page {local_page_number}")
            else:
                conversion_logger.info(f"Processed question {global_question_number} for {subject}")

    return end_question_number + 1

def find_section_folder(ales_exam_folder, section_code):
    """Finds the section folder matching the given section code."""
    normalized_section_code = normalize_string(section_code)
    for folder_name in os.listdir(ales_exam_folder):
        folder_path = os.path.join(ales_exam_folder, folder_name)
        if os.path.isdir(folder_path):
            normalized_folder_name = normalize_string(folder_name)
            if normalized_folder_name == normalized_section_code.lower():
                return folder_path
    return None

def get_subject_folder(base_path, subject, exam_type_upper):
    current_subject_folder_mapping = subject_folder_mapping.get(exam_type_upper, {})
    mapped_subject = current_subject_folder_mapping.get(subject, subject)

    if isinstance(mapped_subject, list):
        for mapped_subj in mapped_subject:
            subject_folder = find_folder_recursively(base_path, mapped_subj)
            if subject_folder:
                return subject_folder
        process_logger.error(f"Subject folder not found for any mapped subjects: {mapped_subject} in {base_path}")
        return None
    else:
        subject_folder = find_folder_recursively(base_path, mapped_subject)
        return subject_folder

# Subject-folder mappings for each exam type
subject_folder_mapping = {
    'AYT': {
        'Türkçe': 'Edebiyat',
        'Edebiyat': 'Edebiyat',
        'Matematik': 'Matematik',
        'Geometri': 'Geometri',
        'Fizik': 'Fizik',
        'Kimya': 'Kimya',
        'Biyoloji': 'Biyoloji',
        'Tarih-1': 'Tarih-1',
        'Coğrafya-1': 'Coğrafya-1',
        'Tarih-2': 'Tarih-2',
        'Coğrafya-2': 'Coğrafya-2',
        'Felsefe': 'Felsefe', 
        'Din Kültürü': 'Din Kültürü',
    },
    'TYT': {
        'Türkçe': 'Türkçe',
        'Matematik': 'Matematik',
        'Geometri': 'Geometri',
        'Fizik': 'Fizik',
        'Kimya': 'Kimya',
        'Biyoloji': 'Biyoloji',
        'Coğrafya': 'Coğrafya',
        'Tarih': 'Tarih',
        'Felsefe': 'Felsefe',
        'Din Kültürü': 'Din Kültürü',
    },
    'ALES': {
        'Matematik': ['Matematik'],
        'Geometri': ['Geometri'],
        'Türkçe': ['Türkçe'],
    },
    'KPSS': {
        'Türkçe': 'Türkçe',
        'Matematik': 'Matematik',
        'Geometri': 'Geometri',
        'Tarih': 'Tarih',
        'Coğrafya': 'Coğrafya',
        'Vatandaşlık': 'Vatandaşlık',
        'Genel Kültür': 'Güncel Bilgiler',
    },
    'MSÜ': {
        'Türkçe': 'TÜRKÇE',
        'Matematik': 'MATEMATİK',
        'Geometri': 'Geometri',
        'Fizik': 'Fizik',
        'Kimya': 'Kimya',
        'Biyoloji': 'Biyoloji',
        'Coğrafya': 'Coğrafya',
        'Tarih': 'Tarih',
        'Felsefe': 'Felsefe',
        'Din Kültürü': 'Din Kültürü ve Ahlak Bilgisi',
    },
    'YDT': {
        'İngilizce': 'İNGİLİZCE',
        'Almanca': 'ALMANCA',
        'Fransızca': 'FRANSIZCA',
        'Arapça': 'ARAPÇA',
        'Rusça': 'RUSÇA',
    },
    'YGS': {
        'Türkçe': 'Türkçe',
        'Matematik': 'MATEMATİK',
        'Geometri': 'GEOMETRİ',
        'Fizik': 'Fizik',
        'Kimya': 'Kimya',
        'Biyoloji': 'Biyoloji',
        'Coğrafya': 'Coğrafya',
        'Tarih': 'Tarih',
        'Felsefe': 'Felsefe',
        'Din Kültürü': 'Din Kültürü ve Ahlak Bilgisi',
    },
    'LYS': {
        'Matematik': 'Matematik',
        'Geometri': 'Geometri',
        'Fizik': 'Fizik',
        'Kimya': 'Kimya',
        'Biyoloji': 'Biyoloji',
        'Tarih': 'Tarih',
        'Tarih-1': 'Tarih-1',
        'Tarih-2': 'Tarih-1',
        'Coğrafya': 'Coğrafya',
        'Coğrafya-1': 'Coğrafya-1',
        'Türkçe': 'Türk Dili ve edebiyatı',
        'Edebiyat': 'Türk Dili ve edebiyatı',
        'Coğrafya-2': 'Coğrafya-2',
        'Sosyoloji': 'Sosyoloji',
        'Psikoloji': 'Psikoloji',
        'Mantık': 'Mantık',
        'Din Kültürü': 'Din Kültürü ve Ahlak Bilgisi',
    },
}

# Subject-section mappings for each exam type
subject_section_mapping = {
    'AYT': {
        'Türkçe': 'turkdili-edebiyat-testi',
        'Edebiyat': 'turkdili-edebiyat-testi',
        'Tarih-1': 'turkdili-edebiyat-testi',
        'Coğrafya-1': 'turkdili-edebiyat-testi',
        'Tarih-2': 'sosyal-testi',
        'Coğrafya-2': 'sosyal-testi',
        'Felsefe': 'sosyal-testi',
        'Psikoloji': 'sosyal-testi',
        'Mantık': 'sosyal-testi',
        'Din Kültürü': 'sosyal-testi',
        'Sosyoloji': 'sosyal-testi',
        'Matematik': 'matematik-testi',
        'Geometri': 'matematik-testi',
        'Fizik': 'fen-testi',
        'Kimya': 'fen-testi',
        'Biyoloji': 'fen-testi',
    },
    'TYT': {
        'Türkçe': 'turkce-testi',
        'Matematik': 'matematik-testi',
        'Geometri': 'matematik-testi',
        'Fizik': 'fen-testi',
        'Kimya': 'fen-testi',
        'Biyoloji': 'fen-testi',
        'Coğrafya': 'sosyal-bilimler-testi',
        'Tarih': 'sosyal-bilimler-testi',
        'Felsefe': 'sosyal-bilimler-testi',
        'Din Kültürü': 'sosyal-bilimler-testi',
    },
    'ALES': {
        # Handled dynamically in process_ales_exam
    },
    'KPSS': {
        'Türkçe': 'genel-yetenek-testi',
        'Matematik': 'genel-yetenek-testi',
        'Geometri': 'genel-yetenek-testi',
        'Tarih': 'genel-kultur-testi',
        'Coğrafya': 'genel-kultur-testi',
        'Vatandaşlık': 'genel-kultur-testi',
        'Genel Kültür': 'genel-kultur-testi',
    },
    'MSÜ': {
        'Türkçe': 'turkce-testi',
        'Matematik': 'matematik-testi',
        'Geometri': 'matematik-testi',
        'Fizik': 'fen-testi',
        'Kimya': 'fen-testi',
        'Biyoloji': 'fen-testi',
        'Coğrafya': 'sosyal-bilimler-testi',
        'Tarih': 'sosyal-bilimler-testi',
        'Felsefe': 'sosyal-bilimler-testi',
        'Din Kültürü': 'sosyal-bilimler-testi',
    },
    'YDT': {
        'İngilizce': 'ingilizce-testi',
        'Almanca': 'almanca-testi',
        'Fransızca': 'fransizca-testi',
        'Arapça': 'arapca-testi',
        'Rusça': 'rusca-testi',
    },
    'YGS': {
        'Türkçe': 'turkce-testi',
        'Matematik': 'matematik-testi',
        'Geometri': 'matematik-testi',
        'Fizik': 'fen-testi',
        'Kimya': 'fen-testi',
        'Biyoloji': 'fen-testi',
        'Coğrafya': 'sosyal-bilimler-testi',
        'Tarih': 'sosyal-bilimler-testi',
        'Felsefe': 'sosyal-bilimler-testi',
        'Din Kültürü': 'sosyal-bilimler-testi',
    },
    'LYS': {
        'Matematik': 'matematik-testi',
        'Geometri': 'geometri-testi',
        'Fizik': 'fizik-testi',
        'Kimya': 'kimya-testi',
        'Biyoloji': 'biyoloji-testi',
        'Tarih': 'tarih-testi',
        'Tarih-1': 'tarih-testi',
        'Tarih-2': 'tarih-testi',
        'Coğrafya': 'cografya-testi',
        'Coğrafya-1': 'cografya-testi',
        'Türkçe': 'turkdili-edebiyat-testi',
        'Edebiyat': 'turkdili-edebiyat-testi',
        'Coğrafya-2': 'cografya-testi',
        'Sosyoloji': 'sosyal-bilimler-testi',
        'Psikoloji': 'sosyal-bilimler-testi',
        'Mantık': 'sosyal-bilimler-testi',
        'Din Kültürü ve Ahlak Bilgisi': 'sosyal-bilimler-testi',
        'Din Kültürü': 'sosyal-bilimler-testi',
    },
}

# Process all exam types
for exam_type in sections_data.keys():
    process_exam(exam_type)
