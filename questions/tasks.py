from celery import shared_task
from .models import ExamYear, ExamType, Subject, Topic, Question
import pandas as pd
from others.models import BulkUploadStatus
from unidecode import unidecode

@shared_task
def process_bulk_upload_questions(df_data, form_data, user_id=None, task_type='questions'):
    # Create a status entry in the database
    task_status, _ = BulkUploadStatus.objects.get_or_create(task_id=process_bulk_upload_questions.request.id, defaults={
        'task_type': task_type,
        'user_id': user_id,
    })

    # Convert back to DataFrame
    df = pd.DataFrame(df_data)

    try:
        total_rows = len(df)
        processed_rows = 0
        created_questions = 0
        updated_questions = 0
        error_messages = []  # Collect all errors
        success_messages = []  # Collect success messages

        # Loop through each row in the data
        for index, row in df.iterrows():
            try:
                # Check required fields
                required_fields = ['exam_year', 'exam_type', 'subject', 'correct_answer', 'question_number']
                skip_row = False
                for field in required_fields:
                    field_value = row[form_data[field]]
                    if pd.isna(field_value) or str(field_value).strip() == '':
                        error_messages.append(f"Satır {index + 1}: '{field}' boş olamaz.")
                        skip_row = True
                        break  # Skip if a required field is missing
                if skip_row:
                    continue  # Skip this row if any required field is invalid

                # Map columns using form data
                exam_year_value = int(str(row[form_data['exam_year']]).strip())
                exam_type_name = str(row[form_data['exam_type']]).strip()
                subject_name = str(row[form_data['subject']]).strip()
                question_number = int(str(row[form_data['question_number']]).strip())
                correct_answer = str(row[form_data['correct_answer']]).strip()

                # Create or get ExamYear
                exam_year, _ = ExamYear.objects.get_or_create(year=exam_year_value)

                # Get or ensure ExamType exists
                exam_type = ExamType.objects.get(name=exam_type_name)

                # Ensure the ExamType is associated with the ExamYear
                if not exam_year.exam_types.filter(id=exam_type.id).exists():
                    exam_year.exam_types.add(exam_type)

                # Get or ensure Subject exists
                subject = Subject.objects.get(name=subject_name)

                # Ensure the Subject is associated with the ExamType
                if not exam_type.subjects.filter(id=subject.id).exists():
                    exam_type.subjects.add(subject)

                # Handle optional fields
                topic = None
                if not form_data['skip_achievement_code'] and form_data['achievement_code']:
                    achievement_code_field = form_data['achievement_code']
                    achievement_code_value = row[achievement_code_field]
                    if not pd.isna(achievement_code_value) and str(achievement_code_value).strip() != '':
                        try:
                            achievement_code = int(str(achievement_code_value).strip())
                            topic = Topic.objects.get(achievement_code=achievement_code)
                            if unidecode(topic.subject.name).lower() != unidecode(subject.name).lower():
                                error_messages.append(f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: Kazanım Kodu {achievement_code} {subject.name} dersine ait değil. {topic.subject.name} dersine ait. Konu atlanacak.")
                                topic = None
                        except (Topic.DoesNotExist, ValueError):
                            error_messages.append(f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: Konu bulunamadı: Kazanım Kodu {achievement_code_value}")
                            topic = None

                # Handle difficulty_level
                difficulty_level = None
                if not form_data['skip_difficulty_level'] and form_data['difficulty_level']:
                    difficulty_level_field = form_data['difficulty_level']
                    difficulty_level_value = row[difficulty_level_field]
                    if not pd.isna(difficulty_level_value) and str(difficulty_level_value).strip() != '':
                        try:
                            difficulty_level = int(difficulty_level_value)
                        except (ValueError, TypeError):
                            error_messages.append(f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: 'Zorluk Seviyesi' sayısal olmalıdır.")
                            difficulty_level = None

                # Handle image_url
                image_url = None
                if not form_data['skip_image_url'] and form_data['image_url']:
                    image_url_field = form_data['image_url']
                    image_url_value = row[image_url_field]
                    if not pd.isna(image_url_value) and str(image_url_value).strip() != '':
                        image_url = str(image_url_value).strip()

                # Handle video_solution_url
                video_solution_url = None

                if not form_data['skip_video_solution_url'] and form_data['video_solution_url']:
                    video_solution_url_field = form_data['video_solution_url']
                    video_solution_url_value = row[video_solution_url_field]
                    
                    # Check if the value is not NaN and not an empty string
                    if not pd.isna(video_solution_url_value) and str(video_solution_url_value).strip() != '':
                        video_solution_url = str(video_solution_url_value).strip()

                # Check if the correct_answer field is too long
                if correct_answer and len(correct_answer) > 1:
                    error_messages.append(f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: 'Doğru Cevap' 1 karakter uzunluğunda olmalıdır.")
                    continue  # Skip this row

                # Check if the question exists, if so, update; otherwise, create a new one
                question, created = Question.objects.get_or_create(
                    exam_year=exam_year,
                    exam_type=exam_type,
                    subject=subject,
                    question_number=question_number,
                    defaults={
                        'topic': topic,
                        'correct_answer': correct_answer,
                        'difficulty_level': difficulty_level,
                        'image_url': image_url,
                        'video_solution_url': video_solution_url,
                    }
                )

                if not created:
                    # Update the existing question's fields
                    if topic is not None and topic != '':
                        question.topic = topic
                    if correct_answer is not None and correct_answer != '':
                        question.correct_answer = correct_answer
                    if difficulty_level is not None and difficulty_level != '':
                        question.difficulty_level = difficulty_level
                    if image_url is not None and image_url != '':
                        question.image_url = image_url
                    if video_solution_url is not None and video_solution_url != '':
                        question.video_solution_url = video_solution_url
                    question.save()
                    updated_questions += 1
                else:
                    created_questions += 1

            except Exception as e:
                # Log the error for this row
                error_messages.append(f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: Bir hata oluştu - {str(e)}")
                error_message = f"Satır {index + 1}, {exam_type} sınav türü, {exam_year} sınav yılı, {subject_name} dersi için: Bir hata oluştu - {str(e)}"
                task_status.message = error_message
                task_status.save()
                continue  # Skip to the next row

            # Update progress
            processed_rows += 1
            progress = int((processed_rows / total_rows) * 100)
            task_status.progress = progress
            task_status.status = 'PROGRESS'
            task_status.save()

        # Update task status to SUCCESS
        task_status.status = 'SUCCESS'
        task_status.message = f"{created_questions} tane soru başarıyla oluşturuldu, {updated_questions} tane soru güncellendi. Yükleme geçmişi sayfasına giderek detayları görebilirsiniz."
        success_messages.append(
            f"{created_questions} tane soru başarıyla oluşturuldu, {updated_questions} tane soru güncellendi.\n"
            f"Uyarılar ve Hatalar: \n" + "\n".join(error_messages)
        )
        task_status.progress = 100
        task_status.save()

    except Exception as e:
        # Update task status to FAILURE
        task_status.status = 'FAILURE'
        task_status.message = f"Hata oluştu: {str(e)}"
        task_status.save()
