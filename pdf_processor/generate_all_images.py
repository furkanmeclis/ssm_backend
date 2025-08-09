import fitz  # PyMuPDF
import re
import os
import logging
import yaml
import numpy as np

def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def find_pdf_config(config, pdf_path):
    for category, content in config.items():
        if isinstance(content, dict):
            # Check if it's the new structure (Category -> Filename -> Details)
            if os.path.basename(pdf_path) in content:
                return content[os.path.basename(pdf_path)]
            
            # Check if it's the old structure (Category -> Subcategory -> Filename -> Details)
            for subcategory, files in content.items():
                if isinstance(files, dict):
                    for filename, details in files.items():
                        if filename == os.path.basename(pdf_path):
                            return details
                        
            # Check if it's the old structure (Category -> Subcategory -> Subcategory -> Filename -> Details)
            for subcategory, subcategories in content.items():
                if isinstance(subcategories, dict):
                    for subcategory2, files in subcategories.items():
                        if isinstance(files, dict):
                            for filename, details in files.items():
                                if filename == os.path.basename(pdf_path):
                                    return details
    
    logging.error(f"No configuration found for {pdf_path}.")
    return None

def setup_logging(log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(message)s')
    open(log_file, 'w').close()

def extract_and_crop_questions(pdf_path, base_output_dir, config, crop_width=247, y_margin=10, x_margin=15, image_dpi=300):
    if not os.path.exists(pdf_path):
        logging.error(f"The file path {pdf_path} does not exist.")
        return
    
    doc = fitz.open(pdf_path)
    pdf_config = find_pdf_config(config, pdf_path)
    
    if not pdf_config or 'sections' not in pdf_config or 'start_text' not in pdf_config:
        logging.error(f"Incomplete configuration for {pdf_path}.")
        return
    
    sections = pdf_config['sections']
    start_text = pdf_config['start_text']

    output_dir = os.path.join(base_output_dir, os.path.splitext(os.path.basename(pdf_path))[0])
    os.makedirs(output_dir, exist_ok=True)

    section_names = list(sections.keys())
    section_index = 0
    start_cropping = False
    question_heights = {}
    processed_questions_summary = {}

    question_pattern = re.compile(r'(\d+)\.\s')
    answer_pattern = re.compile(r'[A-E]\)')

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")

        if start_text in text:
            start_cropping = True
            section_index += 1

        if start_cropping and section_index <= len(section_names):
            section_name = section_names[section_index - 1]
            max_questions = sections[section_name]
            
            if isinstance(max_questions, int):
                matches = list(question_pattern.finditer(text))
                
                if section_name not in processed_questions_summary:
                    processed_questions_summary[section_name] = set()
                    question_heights[section_name] = []
                
                for i, match in enumerate(matches):
                    question_num = int(match.group(1))
                    if question_num > max_questions or question_num in processed_questions_summary[section_name]:
                        continue

                    question_start = match.start()
                    if i + 1 < len(matches):
                        question_end = matches[i + 1].start()
                    else:
                        question_end = len(text)
                    
                    question_text = text[question_start:question_end].strip()
                    
                    question_rects = page.search_for(question_text)
                    
                    if question_rects:
                        question_rect = question_rects[0]
                        x0, y0, _, _ = question_rect

                        blocks = page.get_text("blocks")
                        max_y = y0
                        for b in blocks:
                            bx, by, bw, bh, btext = b[:5]
                            if bx >= x0 and by >= y0 and bw <= x0 + crop_width:
                                answer_matches = list(answer_pattern.finditer(btext))
                                if answer_matches:
                                    last_answer = answer_matches[-1]
                                    max_y = max(max_y, bh)
                                    if last_answer.group() == 'E)':
                                        break
                        
                        if max_y <= y0:
                            continue
                        
                        crop_rect = fitz.Rect(x0 + x_margin, y0, x0 + crop_width, max_y + y_margin)
                        
                        if crop_rect.width > 0 and crop_rect.height > 0:
                            section_dir = os.path.join(output_dir, section_name)
                            os.makedirs(section_dir, exist_ok=True)
                            
                            zoom = image_dpi / 72  
                            matrix = fitz.Matrix(zoom, zoom)  

                            img = page.get_pixmap(matrix=matrix, clip=crop_rect)
                            img.save(f"{section_dir}/{question_num}.png")
                            processed_questions_summary[section_name].add(question_num)
                            
                            question_height = max_y + y_margin - y0
                            question_heights[section_name].append(question_height)
                        else:
                            pass
                    else:
                        pass
            else:
                logging.error(f"Invalid question count for section {section_name}. Expected an integer but got {type(max_questions)}.")

    for section_name, heights in question_heights.items():
        logging.info("------------------------------------------------")
        if heights:
            median_height = np.median(heights)  
            filtered_heights = [h for h in heights if 0.5 * median_height <= h <= 1.5 * median_height]
            if filtered_heights:
                average_height = sum(filtered_heights) / len(filtered_heights)
            else:
                average_height = median_height  

            for i, height in enumerate(heights):
                if height > 1.5 * average_height:
                    logging.warning(f"[{section_name}] Soru {i+1} buyuk. Yukseklik: {round(height, 2)} (ortalama yukseklik: {round(average_height, 2)}).")
                elif height < 0.5 * average_height:
                    logging.warning(f"[{section_name}] Soru {i+1} kucuk. Yukseklik: {round(height, 2)} (ortalama yukseklik: {round(average_height, 2)}).")
                    
    for section_name, max_questions in sections.items():
        if isinstance(max_questions, int):
            missing_questions = set(range(1, max_questions + 1)) - processed_questions_summary.get(section_name, set())
            if missing_questions:
                logging.error("------------------------------------------------")
                logging.error(f"[{section_name}] Eksik sorular: {sorted(missing_questions)}")
        else:
            logging.error(f"Invalid question count for section {section_name}. Expected an integer but got {type(max_questions)}.")

def process_all_pdfs(config, base_input_dir, base_output_dir):
    for category, subcategories in config.items():
        if isinstance(subcategories, dict):
            for subcategory, files in subcategories.items():
                if isinstance(files, dict):
                    for filename in files:
                        pdf_path = os.path.join(base_input_dir, category, subcategory, filename)
                        output_path = os.path.join(base_output_dir, category, subcategory, os.path.splitext(filename)[0])
                        log_file = os.path.join(output_path, "logs", "question_cropping.log")
                        
                        setup_logging(log_file)
                        
                        extract_and_crop_questions(pdf_path, output_path, config)

if __name__ == "__main__":
    config_path = "config.yaml"
    base_input_dir = "/home/atakan/work/osym_backend/EXAM_PDFS"
    base_output_dir = "output"
    
    config = load_config(config_path)
    process_all_pdfs(config, base_input_dir, base_output_dir)
