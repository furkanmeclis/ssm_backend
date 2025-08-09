import fitz  # PyMuPDF
import re
import os
import logging
import yaml
import numpy as np
from PIL import Image, ImageDraw

# Set up logging
log_dir = "logs"
log_file = os.path.join(log_dir, "question_cropping.log")
os.makedirs(log_dir, exist_ok=True)

# Clear log file
open(log_file, 'w').close()

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(message)s')

# Load the configuration file
def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def find_pdf_config(config, pdf_path):
    for category, content in config.items():
        if isinstance(content, dict):
            if os.path.basename(pdf_path) in content:
                return content[os.path.basename(pdf_path)]
            for subcategory, files in content.items():
                if isinstance(files, dict):
                    for filename, details in files.items():
                        if filename == os.path.basename(pdf_path):
                            return details
            for subcategory, subcategories in content.items():
                if isinstance(subcategories, dict):
                    for subcategory2, files in subcategories.items():
                        if isinstance(files, dict):
                            for filename, details in files.items():
                                if filename == os.path.basename(pdf_path):
                                    return details
    logging.error(f"{pdf_path} için yapılandırma bulunamadı.")
    return None

def extract_and_crop_questions(pdf_path, base_output_dir, crop_width=247, y_margin=10, x_margin=0, image_dpi=300):
    if not os.path.exists(pdf_path):
        logging.error(f"Dosya yolu {pdf_path} mevcut değil.")
        return
    
    doc = fitz.open(pdf_path)
    config = load_config()
    pdf_config = find_pdf_config(config, pdf_path)
    
    if not pdf_config or 'sections' not in pdf_config or 'start_text' not in pdf_config:
        logging.error(f"{pdf_path} için eksik yapılandırma.")
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
    skip_until_first_question = False

    question_pattern = re.compile(r'(\d+)\.\s')
    answer_pattern = re.compile(r'[A-E]\)')

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")

        if start_text in text:
            start_cropping = True
            section_index += 1
            skip_until_first_question = True

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
                    
                    if skip_until_first_question:
                        if question_num != 1:
                            continue
                        else:
                            skip_until_first_question = False

                    if question_num > max_questions or question_num in processed_questions_summary[section_name]:
                        continue

                    question_start = match.start()
                    if i + 1 < len(matches):
                        question_end = matches[i + 1].start()
                    else:
                        question_end = len(text)
                    
                    question_text = text[question_start:question_end].strip()
                    
                    question_rects = page.search_for(question_text)

                    logging.info(f"question_num: {question_num}, question_text: {question_text}, question_rects: {question_rects}")
                    
                    if question_rects:
                        question_rect = question_rects[0]
                        x0, y0, _, _ = question_rect

                        start_text_rects = page.search_for(start_text)
                        if start_text_rects:
                            _, start_y0, _, start_y1 = start_text_rects[0]
                            if y0 <= start_y1:
                                skip_until_first_question = True
                                continue

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
                            
                            img_pil = Image.frombytes("RGB", [img.width, img.height], img.samples)
                            draw = ImageDraw.Draw(img_pil)
                            
                            # Mask the top left section of the question number with a white square
                            mask_width = 50  # Width of the square mask
                            mask_height = 50  # Height of the square mask
                            draw.rectangle([0, 0, mask_width, mask_height], fill="white")
                            
                            img_pil.save(f"{section_dir}/{question_num}.png")
                            processed_questions_summary[section_name].add(question_num)

                            question_height = max_y + y_margin - y0
                            question_heights[section_name].append(question_height)
                        else:
                            pass
                    else:
                        pass
            else:
                logging.error(f"{section_name} bölümü için geçersiz soru sayısı. Bir tam sayı bekleniyordu ancak {type(max_questions)} alındı.")

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
            logging.error(f"{section_name} bölümü için geçersiz soru sayısı. Bir tam sayı bekleniyordu ancak {type(max_questions)} alındı.")

if __name__ == "__main__":
    pdf_path = "/home/atakan/work/osym_backend/EXAM_PDFS/KPSS/2021-KPSS/2021-KPSS LİSANS GY-GK.pdf"
    base_output_dir = "output"
    
    extract_and_crop_questions(pdf_path, base_output_dir)
