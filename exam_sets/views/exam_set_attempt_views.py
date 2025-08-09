from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from exam_sets.models import ExamSetQuiz, ExamSetQuizGroup, ExamSetQuizAttempt, ExamSetIncorrectQuestion, ExamSetDisplaySet, ExamSetDisplaySetAttempt, ExamSetDisplaySetIncorrectQuestion
from questions.models import Question
from serializers.exam_set_serializers import *
from utils.api_responses import ApiResponse
from pagination.custom_pagination import CustomPagination
from django.db import transaction
from quizzes.models import FavoriteQuestion
from quizzes.views.attempt_views import get_motivational_message

class SubmitExamSetQuizAttempt(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        user = request.user
        data = request.data
        answers = data.get('answers', [])

        if not answers or not isinstance(answers, list):
            return ApiResponse.BadRequest(message='Geçersiz cevaplar. Lütfen doğru formatta cevaplar gönderin.')

        try:
            quiz = ExamSetQuiz.objects.get(pk=quiz_id, quiz_group__created_by=user)
        except ExamSetQuiz.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav bulunamadı.')
        except ExamSetQuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav grubu bulunamadı.')

        # Get the ordered subjects with their order
        ordered_subject_ids = []
        if quiz.quiz_group and quiz.quiz_group.exam_set:
            ordered_subjects = quiz.quiz_group.exam_set.examsetsubject_set.all().order_by('order')
            ordered_subject_ids = [item.subject_id for item in ordered_subjects]
        
        # Get all questions first
        all_questions = list(quiz.questions.all())
        
        # Sort questions manually based on subject order and question_number
        def sort_key(question):
            try:
                subject_order = ordered_subject_ids.index(question.subject_id)
            except ValueError:
                subject_order = len(ordered_subject_ids)  # Put unordered subjects at the end
            return (subject_order, question.question_number)
        
        quiz_questions = sorted(all_questions, key=sort_key)

        quiz_question_ids = set(quiz.questions.values_list('id', flat=True))
        submitted_question_ids = {answer['question_id'] for answer in answers}
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        details = {'answers': []}

        with transaction.atomic():
            quiz_attempt = ExamSetQuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                correct_count=0,
                incorrect_count=0,
                unanswered_count=0,
                details=details
            )

            incorrect_questions = []

            for answer in answers:
                question_id = answer.get('question_id', None)
                user_answer = answer.get('user_answer', None)
                user_time = answer.get('user_time', None)

                if question_id not in quiz_question_ids:
                    continue

                question = Question.objects.get(pk=question_id)
                correct_answer = question.correct_answer
                is_correct = (user_answer == correct_answer)
                question_order = quiz_questions.index(question) + 1

                if user_answer is None:
                    unanswered_count += 1
                elif is_correct:
                    correct_count += 1
                else:
                    incorrect_count += 1

                if user_answer is None or not is_correct:
                    incorrect_questions.append(
                        ExamSetIncorrectQuestion(
                            user=user,
                            question=question,
                            user_answer=user_answer,
                            user_time=user_time,
                            quiz_attempt=quiz_attempt,
                            question_order=question_order,
                            correct_answer=question.correct_answer
                        )
                    )

                details['answers'].append({
                    'question_id': question_id,
                    'exam_year': {'id': question.exam_year.id, 'year': question.exam_year.year},
                    'exam_type': {'id': question.exam_type.id, 'name': question.exam_type.name},
                    'difficulty_level': question.difficulty_level,
                    'question_order': question_order,
                    'image_url': question.image_url,
                    'video_solution_url': question.video_solution_url,
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'user_time': user_time,
                })

            # Handle unanswered questions separately
            missing_question_ids = quiz_question_ids - submitted_question_ids
            for question_id in missing_question_ids:
                question = Question.objects.get(pk=question_id)
                question_order = quiz_questions.index(question) + 1
                unanswered_count += 1
                incorrect_questions.append(
                    ExamSetIncorrectQuestion(
                        user=user,
                        question=question,
                        user_answer=None,
                        user_time=None,
                        quiz_attempt=quiz_attempt,
                        question_order=question_order,
                        correct_answer=question.correct_answer
                    )
                )
                details['answers'].append({
                    'question_id': question_id,
                    'exam_year': {'id': question.exam_year.id, 'year': question.exam_year.year},
                    'exam_type': {'id': question.exam_type.id, 'name': question.exam_type.name},
                    'difficulty_level': question.difficulty_level,
                    'question_order': question_order,
                    'image_url': question.image_url,
                    'video_solution_url': question.video_solution_url,
                    'user_answer': None,
                    'correct_answer': question.correct_answer,
                    'is_correct': False,
                    'user_time': None
                })

            # Bulk create all incorrect questions at once
            ExamSetIncorrectQuestion.objects.bulk_create(incorrect_questions)

            # Calculate the success rate
            success_rate = (correct_count / len(quiz_questions)) * 100 if len(quiz_questions) > 0 else 0

            # Get motivational message
            motivational_message = get_motivational_message(success_rate, ordered_subject_ids)

            # Update the counts and save the quiz attempt
            quiz_attempt.correct_count = correct_count
            quiz_attempt.incorrect_count = incorrect_count
            quiz_attempt.unanswered_count = unanswered_count
            quiz_attempt.details = details
            quiz_attempt.success_rate = success_rate
            quiz_attempt.motivational_message = motivational_message
            quiz_attempt.save()

        # Add 'is_favorite' to the response data without saving it
        response_details = details.copy()
        for answer in response_details['answers']:
            answer['is_favorite'] = FavoriteQuestion.objects.filter(
                user=user,
                question_id=answer['question_id']
            ).exists()

        response_details['answers'] = sorted(response_details['answers'], key=lambda x: x['question_order'])

        return ApiResponse.Success(message='Sınav başarıyla gönderildi.', data={
            'id': quiz_attempt.id,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'unanswered_count': unanswered_count,
            'details': response_details,
            'motivational_message': motivational_message
        })

class ExamSetQuizAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            quiz_attempt = ExamSetQuizAttempt.objects.get(pk=pk, user=request.user)
        except ExamSetQuizAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav denemesi bulunamadı.')

        serializer = DetailedExamSetQuizAttemptSerializer(quiz_attempt, context={'request': request})
        return ApiResponse.Success(data=serializer.data)
    
    def delete(self, request, pk):
        try:
            quiz_attempt = ExamSetQuizAttempt.objects.get(pk=pk, user=request.user)
            quiz_attempt.delete()
            return ApiResponse.Success(message='Sınav denemesi başarıyla silindi.')
        except ExamSetQuizAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav denemesi bulunamadı.')

class ExamSetQuizGroupAttemptsView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, quiz_group_id):
        try:
            quiz_group = ExamSetQuizGroup.objects.get(pk=quiz_group_id, created_by=request.user)
        except ExamSetQuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav grubu bulunamadı.')

        quizzes = ExamSetQuiz.objects.filter(quiz_group=quiz_group)
        attempts_data = []

        paginator = CustomPagination()

        for quiz in quizzes:
            attempts = ExamSetQuizAttempt.objects.filter(quiz=quiz, user=request.user)
            paginated_attempts = paginator.paginate_queryset(attempts, request)

            serializer = ExamSetQuizAttemptSummarySerializer(paginated_attempts, many=True, context={'request': request})
            attempts_data.append({
                'quiz_id': quiz.id,
                'quiz_name': quiz_group.name,
                'attempts': serializer.data
            })

        return paginator.get_paginated_response(attempts_data)

class ExamSetQuizAttemptListView(generics.ListAPIView):
    serializer_class = ExamSetQuizAttemptSummarySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExamSetQuizAttempt.objects.filter(user=self.request.user)

class ExamSetQuizIDAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, quiz_id):
        try:
            quiz = ExamSetQuiz.objects.get(pk=quiz_id)
        except ExamSetQuiz.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav bulunamadı.')

        attempts = ExamSetQuizAttempt.objects.filter(quiz=quiz, user=request.user)
        paginator = CustomPagination()
        paginated_attempts = paginator.paginate_queryset(attempts, request)

        serializer = DetailedExamSetQuizAttemptSerializer(paginated_attempts, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)

class SubmitExamSetDisplaySet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, display_set_id):
        user = request.user
        data = request.data
        answers = data.get('answers', [])

        if not answers or not isinstance(answers, list):
            return ApiResponse.BadRequest(message='Geçersiz cevaplar. Lütfen doğru formatta cevaplar gönderin.')

        try:
            display_set = ExamSetDisplaySet.objects.get(pk=display_set_id, created_by=user)
        except ExamSetDisplaySet.DoesNotExist:
            return ApiResponse.NotFound(message='Soru seti bulunamadı.')

        # Get the ordered subjects with their order
        ordered_subject_ids = []
        if display_set.exam_set:
            ordered_subjects = display_set.exam_set.examsetsubject_set.all().order_by('order')
            ordered_subject_ids = [item.subject_id for item in ordered_subjects]
        
        # Get all questions first
        all_questions = list(display_set.questions.all())
        
        # Sort questions manually based on subject order and question_number
        def sort_key(question):
            try:
                subject_order = ordered_subject_ids.index(question.subject_id)
            except ValueError:
                subject_order = len(ordered_subject_ids)  # Put unordered subjects at the end
            return (subject_order, question.question_number)
        
        questions = sorted(all_questions, key=sort_key)

        total_questions = len(questions)

        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        details = {'answers': []}

        with transaction.atomic():
            # Create the display set attempt
            display_set_attempt = ExamSetDisplaySetAttempt.objects.create(
                user=user,
                display_set=display_set,
                correct_count=0,
                incorrect_count=0,
                unanswered_count=0,
                details=details
            )

            incorrect_questions = []

            for answer in answers:
                question_order = answer.get('question_order')

                # Skip invalid orders
                if question_order is None or not (1 <= question_order <= total_questions):
                    continue

                # Get the question using the order
                question = questions[question_order - 1]
                user_answer = answer.get('user_answer')
                user_time = answer.get('user_time')
                correct_answer = question.correct_answer
                is_correct = (user_answer == correct_answer)

                if user_answer is None:
                    unanswered_count += 1
                elif is_correct:
                    correct_count += 1
                else:
                    incorrect_count += 1

                if user_answer is None or not is_correct:
                    incorrect_questions.append(
                        ExamSetDisplaySetIncorrectQuestion(
                            user=user,
                            question=question,
                            user_answer=user_answer,
                            user_time=user_time,
                            display_set_attempt=display_set_attempt,
                            question_order=question_order,
                            correct_answer=question.correct_answer
                        )
                    )

                details['answers'].append({
                    'id': question.id,
                    'question_order': question_order,
                    'exam_year': {'id': question.exam_year.id, 'year': question.exam_year.year},
                    'exam_type': {'id': question.exam_type.id, 'name': question.exam_type.name},
                    'difficulty_level': question.difficulty_level,
                    'image_url': question.image_url,
                    'video_solution_url': question.video_solution_url,
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'user_time': user_time,
                })

            # Handle unanswered questions
            submitted_orders = {answer.get('question_order') for answer in answers if 'question_order' in answer}
            missing_orders = set(range(1, total_questions + 1)) - submitted_orders

            for question_order in missing_orders:
                question = questions[question_order - 1]
                unanswered_count += 1

                incorrect_questions.append(
                    ExamSetDisplaySetIncorrectQuestion(
                        user=user,
                        question=question,
                        user_answer=None,
                        user_time=None,
                        display_set_attempt=display_set_attempt,
                        question_order=question_order,
                        correct_answer=question.correct_answer
                    )
                )

                details['answers'].append({
                    'id': question.id,
                    'question_order': question_order,
                    'exam_year': {'id': question.exam_year.id, 'year': question.exam_year.year},
                    'exam_type': {'id': question.exam_type.id, 'name': question.exam_type.name},
                    'difficulty_level': question.difficulty_level,
                    'image_url': question.image_url,
                    'video_solution_url': question.video_solution_url,
                    'user_answer': None,
                    'correct_answer': question.correct_answer,
                    'is_correct': False,
                    'user_time': None,
                })

            # Bulk create all incorrect questions at once
            ExamSetDisplaySetIncorrectQuestion.objects.bulk_create(incorrect_questions)

            # Calculate the success rate
            success_rate = (correct_count / total_questions) * 100 if total_questions > 0 else 0

            # Get motivational message
            motivational_message = get_motivational_message(success_rate, ordered_subject_ids)

            # Update the counts and save the display set attempt
            display_set_attempt.correct_count = correct_count
            display_set_attempt.incorrect_count = incorrect_count
            display_set_attempt.unanswered_count = unanswered_count
            display_set_attempt.details = details
            display_set_attempt.success_rate = success_rate
            display_set_attempt.motivational_message = motivational_message
            display_set_attempt.save()

        # Add 'is_favorite' to the response data without saving it
        response_details = details.copy()
        for answer in response_details['answers']:
            answer['is_favorite'] = FavoriteQuestion.objects.filter(
                user=user,
                question_id=answer['id']
            ).exists()

        return ApiResponse.Success(message='Soru seti başarıyla gönderildi.', data={
            'id': display_set_attempt.id,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'unanswered_count': unanswered_count,
            'details': response_details,
            'motivational_message': motivational_message
        })

class ExamSetDisplaySetAttemptListView(generics.ListAPIView):
    serializer_class = ExamSetDisplaySetAttemptSummarySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExamSetDisplaySetAttempt.objects.filter(user=self.request.user)

class ExamSetDisplaySetAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            display_set_attempt = ExamSetDisplaySetAttempt.objects.get(pk=pk, user=request.user)
        except ExamSetDisplaySetAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='PDF denemesi bulunamadı.')

        serializer = DetailedExamSetDisplaySetAttemptSerializer(display_set_attempt, context={'request': request})
        return ApiResponse.Success(data=serializer.data)
    
    def delete(self, request, pk):
        try:
            display_set_attempt = ExamSetDisplaySetAttempt.objects.get(pk=pk, user=request.user)
            display_set_attempt.delete()
            return ApiResponse.Success(message='PDF denemesi başarıyla silindi.')
        except ExamSetDisplaySetAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='PDF denemesi bulunamadı.')

class ExamSetDisplaySetIDAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, display_set_id):
        try:
            display_set = ExamSetDisplaySet.objects.get(pk=display_set_id)
        except ExamSetDisplaySet.DoesNotExist:
            return ApiResponse.NotFound(message='PDF bulunamadı.')

        attempts = ExamSetDisplaySetAttempt.objects.filter(display_set=display_set, user=request.user)
        paginator = CustomPagination()
        paginated_attempts = paginator.paginate_queryset(attempts, request)

        serializer = DetailedExamSetDisplaySetAttemptSerializer(paginated_attempts, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)
