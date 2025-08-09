from celery import shared_task
from .models import University, Major, Program, ExamYear, Location
import pandas as pd
import re
from others.models import BulkUploadStatus
import unicodedata

def clean_column_name(column):
    """Normalize, clean, and format column names."""
    # Normalize Unicode characters (NFKC)
    column = unicodedata.normalize("NFKC", column)
    
    # Remove non-printable characters
    column = ''.join(c for c in column if not unicodedata.category(c).startswith('C'))
    
    # Replace newlines and excessive spaces
    column = column.replace('\n', ' ').replace('\r', '').strip()
    
    # Ensure there is a space between numbers and letters (e.g., '2024TABAN' -> '2024 TABAN')
    column = re.sub(r'(\d)([A-Za-z])', r'\1 \2', column)
    
    # Replace multiple spaces with a single space
    column = re.sub(r'\s+', ' ', column)
    return column

def get_value_from_row(row, column_name):
    """Fetch a value from the DataFrame row using a cleaned column name."""
    column_name = clean_column_name(column_name)
    try:
        return row[column_name]
    except KeyError:
        print(f"Column '{column_name}' not found in DataFrame. Available columns: {row.index.tolist()}")
        return None

@shared_task(bind=True)
def process_bulk_upload_uni_rankings(self, df_data, form_data):
    # Create a status entry in the database
    task_status, _ = BulkUploadStatus.objects.get_or_create(task_id=self.request.id)
    task_status.task_type = 'uni_rankings'  # Specify that this task is for uni_rankings
    task_status.save()

    # Convert back to DataFrame
    df = pd.DataFrame(df_data)

    # Apply the cleaning function to all column names in the DataFrame
    df.columns = [clean_column_name(col) for col in df.columns]
    print("Cleaned Excel Columns:", df.columns.tolist())

    try:
        # Updated list of Turkish city names, including additional cities
        turkish_cities = [
            'ADANA', 'ADIYAMAN', 'AFYONKARAHİSAR', 'AĞRI', 'AMASYA', 'ANKARA',
            'ANTALYA', 'ARTVİN', 'AYDIN', 'BALIKESİR', 'BİLECİK', 'BİNGÖL',
            'BİTLİS', 'BOLU', 'BURDUR', 'BURSA', 'ÇANAKKALE', 'ÇANKIRI',
            'ÇORUM', 'DENİZLİ', 'DİYARBAKIR', 'EDİRNE', 'ELAZIĞ', 'ERZİNCAN',
            'ERZURUM', 'ESKİŞEHİR', 'GAZİANTEP', 'GEBZE', 'GİRESUN', 'GÜMÜŞHANE',
            'HAKKARİ', 'HATAY', 'ISPARTA', 'MERSİN', 'İSTANBUL', 'İZMİR',
            'KARS', 'KASTAMONU', 'KAYSERİ', 'KIRKLARELİ', 'KIRŞEHİR', 'KOCAELİ',
            'KONYA', 'KÜTAHYA', 'MALATYA', 'MANİSA', 'KAHRAMANMARAŞ', 'MARDİN',
            'MUĞLA', 'MUŞ', 'NEVŞEHİR', 'NİĞDE', 'ORDU', 'RİZE', 'SAKARYA',
            'SAMSUN', 'SİİRT', 'SİNOP', 'SİVAS', 'TEKİRDAĞ', 'TOKAT', 'TRABZON',
            'TUNCELİ', 'ŞANLIURFA', 'UŞAK', 'VAN', 'YOZGAT', 'ZONGULDAK',
            'AKSARAY', 'BAYBURT', 'KARAMAN', 'KIRIKKALE', 'BATMAN', 'ŞIRNAK',
            'BARTIN', 'ARDAHAN', 'IĞDIR', 'YALOVA', 'KARABÜK', 'KİLİS',
            'OSMANİYE', 'DÜZCE', 'İÇİŞLERİ BAKANLIĞI VE MİLLİ SAVUNMA BAKANLIĞI ADINA SAĞLIK BİLİMLERİ ÜNİVERSİTESİNDE EĞİTİM ALACAKLAR'
        ]

        university_regex = r'\b(UNIVERSITY|UNIVERSITE|ÜNİVERSİTE|UNIVERSITESI|universite|üniversite|üniversitesi|university)\b'

        # Get the manually entered exam year
        exam_year_value = int(form_data['exam_year'])
        exam_year, _ = ExamYear.objects.get_or_create(year=exam_year_value)

        # Preprocess to determine total_rows
        current_university = None
        rows_to_process = []
        error_messages = []  # Collect all errors
        success_messages = []  # Collect success messages

        for _, row in df.iterrows():
            university_or_major_name = str(row[form_data['university_name']]).strip()

            # Skip entries starting with an asterisk
            if university_or_major_name.startswith('*'):
                continue

            # Check if it's a university row using regex
            if re.search(university_regex, university_or_major_name, re.IGNORECASE):
                current_university = university_or_major_name
                continue  # Move to the next row

            if not current_university:
                continue  # No university context, skip

            university_name = row.get(form_data['university_name'], None)
            if university_name is not None and not pd.isna(university_name):
                rows_to_process.append((current_university, row))

        total_rows = len(rows_to_process)
        processed_rows = 0
        created_universities = 0
        created_programs = 0
        updated_programs = 0

        created_university_ids = set()

        # Now process the rows
        for current_university_name, row in rows_to_process:
            # Detect the location
            location = None
            current_university_upper = current_university_name.upper()

            if 'UOLP' in current_university_upper:
                # Existing UOLP handling logic...
                uolp_match = re.search(r'UOLP-([^)]*)', current_university_name)
                if uolp_match:
                    location_name = f"UOLP-Programları"
                    location, _ = Location.objects.get_or_create(name=location_name)
            else:
                # Step 1: Check for Turkish cities in the university name itself
                university_name_cleaned = re.sub(r'\bÜNİVERSİTE(Sİ)?\b', '', current_university_upper)
                city_found_in_name = False
                for city in turkish_cities:
                    if city in university_name_cleaned:
                        location_name = capitalize_turkish(city)
                        location, _ = Location.objects.get_or_create(name=location_name)
                        city_found_in_name = True
                        break  # Exit if a city is found in the university name
                
                if not city_found_in_name:
                    # Step 2: Check within parentheses
                    parentheses_contents = re.findall(r'\((.*?)\)', current_university_name)
                    
                    possible_locations = []
                    
                    for content in parentheses_contents:
                        content_upper = content.upper().strip()
                        # Skip any content that includes 'ÜNİVERSİTE' or 'ÜNİVERSİTESİ'
                        if 'ÜNİVERSİTE' in content_upper:
                            continue
                        # If content is in turkish cities, use it as location
                        if content_upper in turkish_cities:
                            possible_locations.append(content.strip())
                            break  # Stop after finding the first valid city
                        else:
                            # For foreign or special locations
                            possible_locations.append(content.strip())
                            break  # Stop after finding the first valid location
                    
                    if possible_locations:
                        # Step 3: Use the first found location from parentheses
                        location_name = capitalize_turkish(possible_locations[0])
                        location, _ = Location.objects.get_or_create(name=location_name)

            # Get or create the university
            current_university, uni_created = University.objects.get_or_create(name=current_university_name)
            if uni_created or current_university.id not in created_university_ids:
                if uni_created:
                    created_universities += 1
                created_university_ids.add(current_university.id)

            # Handle Major
            major_name = str(row[form_data['university_name']]).strip()
            major, _ = Major.objects.get_or_create(name=major_name)

            # Handle optional fields with format validation
            program_code = clean_column_name(row, form_data['program_code']) if not form_data['skip_program_code'] else None
            program_code = int(program_code) if program_code and str(program_code).isdigit() else None

            ranking = get_value_from_row(row, form_data['ranking']) if not form_data['skip_ranking'] else None
            min_score = get_value_from_row(row, form_data['min_score']) if not form_data['skip_min_score'] else None
            max_score = get_value_from_row(row, form_data['max_score']) if not form_data['skip_max_score'] else None

            print(f"Ranking (raw): {ranking}")
            print(f"Min Score (raw): {min_score}")
            print(f"Max Score (raw): {max_score}")

            # Clean and convert ranking
            if ranking:
                ranking = re.sub(r'[,.]', '', str(ranking))
                ranking = int(ranking) if ranking.isdigit() else None

            # Convert min_score and max_score to floats
            if min_score:
                min_score = float(str(min_score).replace(',', '.')) if re.match(r'^\d+(\.\d+)?$', str(min_score).replace(',', '.')) else None

            if max_score:
                max_score = float(str(max_score).replace(',', '.')) if re.match(r'^\d+(\.\d+)?$', str(max_score).replace(',', '.')) else None

            # Handle program_type and education_length
            program_type = clean_column_name(row, form_data['program_type']) if not form_data['skip_program_type'] else None
            program_type = str(program_type).strip() if program_type else None

            education_length = clean_column_name(row, form_data['education_length']) if not form_data['skip_education_length'] else None
            education_length = int(education_length) if education_length and str(education_length).isdigit() else None

            # Create or update Program
            program_defaults = {
                'ranking': ranking,
                'program_code': program_code,
                'min_score': min_score,
                'max_score': max_score,
                'program_type': program_type,
                'education_length': education_length,
            }
            if location:
                program_defaults['location'] = location

            program, created = Program.objects.update_or_create(
                major=major,
                university=current_university,
                exam_year=exam_year,
                defaults=program_defaults
            )
            if created:
                created_programs += 1
            else:
                updated_programs += 1

            # Update progress
            processed_rows += 1
            progress = int((processed_rows / total_rows) * 100)
            task_status.progress = progress
            task_status.status = 'PROGRESS'
            task_status.save()

        # Update task status to SUCCESS
        task_status.status = 'SUCCESS'
        task_status.message = f"{created_programs} program ve {created_universities} üniversite başarıyla {exam_year_value} yılı için yüklendi. {updated_programs} program güncellendi. Yükleme geçmişi sayfasına giderek detayları görebilirsiniz."
        success_messages.append(task_status.message)
        task_status.progress = 100
        task_status.save()

    except Exception as e:
        # Update task status to FAILURE
        task_status.status = 'FAILURE'
        task_status.message = f"Hata oluştu: {str(e)}"
        error_messages.append(task_status.message)
        task_status.save()

def capitalize_turkish(text):
    import unicodedata

    # Normalize the text to NFC form to handle combined characters properly
    text = unicodedata.normalize('NFC', text.strip())

    if not text:
        return text

    # Mappings for Turkish-specific lowercase to uppercase
    tr_lower_to_upper = {
        'a': 'A', 'b': 'B', 'c': 'C', 'ç': 'Ç',
        'd': 'D', 'e': 'E', 'f': 'F', 'g': 'G',
        'ğ': 'Ğ', 'h': 'H', 'ı': 'I', 'i': 'İ',
        'j': 'J', 'k': 'K', 'l': 'L', 'm': 'M',
        'n': 'N', 'o': 'O', 'ö': 'Ö', 'p': 'P',
        'r': 'R', 's': 'S', 'ş': 'Ş', 't': 'T',
        'u': 'U', 'ü': 'Ü', 'v': 'V', 'y': 'Y',
        'z': 'Z',
    }

    # Mappings for Turkish-specific uppercase to lowercase
    tr_upper_to_lower = {
        'A': 'a', 'B': 'b', 'C': 'c', 'Ç': 'ç',
        'D': 'd', 'E': 'e', 'F': 'f', 'G': 'g',
        'Ğ': 'ğ', 'H': 'h', 'I': 'ı', 'İ': 'i',
        'J': 'j', 'K': 'k', 'L': 'l', 'M': 'm',
        'N': 'n', 'O': 'o', 'Ö': 'ö', 'P': 'p',
        'R': 'r', 'S': 's', 'Ş': 'ş', 'T': 't',
        'U': 'u', 'Ü': 'ü', 'V': 'v', 'Y': 'y',
        'Z': 'z',
    }

    # Capitalize the first character
    first_char = text[0]
    if first_char in tr_lower_to_upper:
        first_char = tr_lower_to_upper[first_char]
    else:
        # Non-letter or already uppercase
        pass

    # Lowercase the rest of the characters
    rest_chars = []
    for c in text[1:]:
        if c in tr_upper_to_lower:
            c = tr_upper_to_lower[c]
        else:
            # Non-letter or already lowercase
            pass
        rest_chars.append(c)

    rest = ''.join(rest_chars)

    return first_char + rest
