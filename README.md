pip-compile requirements.in

docker compose --profile dev up

docker compose --profile prod up -d --build

### pdf_processor:

Inside generate_all_images.py: This script generates all the images from the PDFs in the 'base_input_dir' folder and saves them in the output folder. It retrieves the names, paths, question counts for each section, and starting text from the config.yaml file.

start_text: This text is used to identify the start of the section.