import os
import shutil

def clear_questions(output_dir):
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            shutil.rmtree(os.path.join(root, dir))

if __name__ == "__main__":
    output_dir = "extracted_images"
    clear_questions(output_dir)
