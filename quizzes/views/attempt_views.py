from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from questions.models import Question
from quizzes.models import QuizGroup, Quiz, QuizAttempt, IncorrectQuestion, FavoriteQuestion, QuestionDisplaySet, MotivationalMessage, DisplaySetAttempt, DisplaySetIncorrectQuestion, MultiSubjectMotivationalMessage
from rest_framework import generics
from serializers.quiz_serializers import QuizAttemptSummarySerializer, DetailedQuizAttemptSerializer
from utils.api_responses import ApiResponse
from pagination.custom_pagination import CustomPagination
from django.db import transaction

class SubmitQuizAttempt(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        user = request.user
        data = request.data
        answers = data.get('answers', [])

        if not answers or not isinstance(answers, list):
            return ApiResponse.BadRequest(message='Geçersiz cevaplar. Lütfen doğru formatta cevaplar gönderin.')

        try:
            quiz = Quiz.objects.get(pk=quiz_id, quiz_group__created_by=user)
        except Quiz.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav bulunamadı.')
        except QuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav grubu bulunamadı.')

        quiz_questions = list(quiz.questions.all())
        quiz_question_ids = set(quiz.questions.values_list('id', flat=True))
        submitted_question_ids = {answer['question_id'] for answer in answers}
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        details = {'answers': []}

        with transaction.atomic():
            quiz_attempt = QuizAttempt.objects.create(
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
                        IncorrectQuestion(
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
                    IncorrectQuestion(
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
            IncorrectQuestion.objects.bulk_create(incorrect_questions)

            # Calculate the success rate
            success_rate = (correct_count / len(quiz_questions)) * 100 if len(quiz_questions) > 0 else 0

            subject_id = None
            if hasattr(quiz.quiz_group, 'subject') and quiz.quiz_group.subject:
                subject_id = quiz.quiz_group.subject.id
            else:
                # Try to get subject from questions if quiz_group has no subject
                subjects = set(q.subject_id for q in quiz_questions if q.subject_id)
                if len(subjects) == 1:
                    subject_id = list(subjects)[0]
                elif len(subjects) > 1:
                    subject_id = list(subjects)  # Multiple subjects - pass as list

            # Get motivational message
            motivational_message = get_motivational_message(success_rate, subject_id)

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

        return ApiResponse.Success(message='Sınav başarıyla gönderildi.', data={
            'id': quiz_attempt.id,
            'success_rate': success_rate,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'unanswered_count': unanswered_count,
            'details': response_details,
            'motivational_message': motivational_message
        })

class QuizAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DetailedQuizAttemptSerializer

    def get(self, request, pk):
        try:
            quiz_attempt = QuizAttempt.objects.get(pk=pk, user=request.user)
        except QuizAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav denemesi bulunamadı.')

        serializer = DetailedQuizAttemptSerializer(quiz_attempt, context={'request': request})
        return ApiResponse.Success(data=serializer.data)
    
    def delete(self, request, pk):
        try:
            quiz_attempt = QuizAttempt.objects.get(pk=pk, user=request.user)
            quiz_attempt.delete()
            return ApiResponse.Success(message='Sınav denemesi başarıyla silindi.')
        except QuizAttempt.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav denemesi bulunamadı.')

class QuizGroupAttemptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_group_id):
        try:
            quiz_group = QuizGroup.objects.get(pk=quiz_group_id, created_by=request.user)
        except QuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav grubu bulunamadı.')

        quizzes = Quiz.objects.filter(quiz_group=quiz_group)
        attempts_data = []

        paginator = CustomPagination()

        for quiz in quizzes:
            attempts = QuizAttempt.objects.filter(quiz=quiz, user=request.user)
            paginated_attempts = paginator.paginate_queryset(attempts, request)

            serializer = QuizAttemptSummarySerializer(paginated_attempts, many=True, context={'request': request})
            attempts_data.append({
                'quiz_id': quiz.id,
                'quiz_name': quiz_group.name,
                'attempts': serializer.data
            })

        return paginator.get_paginated_response(attempts_data)

class QuizAttemptListView(generics.ListAPIView):
    serializer_class = QuizAttemptSummarySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

class QuizIDAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = DetailedQuizAttemptSerializer

    def get(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav bulunamadı.')

        attempts = QuizAttempt.objects.filter(quiz=quiz, user=request.user)
        paginator = CustomPagination()
        paginated_attempts = paginator.paginate_queryset(attempts, request)

        serializer = DetailedQuizAttemptSerializer(paginated_attempts, many=True, context={'request': request})

        return paginator.get_paginated_response(serializer.data)

class SubmitDisplaySet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, display_set_id):
        user = request.user
        data = request.data
        answers = data.get('answers', [])

        if not answers or not isinstance(answers, list):
            return ApiResponse.BadRequest(message='Geçersiz cevaplar. Lütfen doğru formatta cevaplar gönderin.')

        try:
            display_set = QuestionDisplaySet.objects.get(pk=display_set_id, created_by=user)
        except QuestionDisplaySet.DoesNotExist:
            return ApiResponse.NotFound(message='Soru seti bulunamadı.')

        # Fetch and order questions by 'id'
        questions = list(display_set.questions.all().order_by('id'))
        total_questions = len(questions)

        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        details = {'answers': []}

        with transaction.atomic():
            # Create the display set attempt
            display_set_attempt = DisplaySetAttempt.objects.create(
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
                        DisplaySetIncorrectQuestion(
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
                    DisplaySetIncorrectQuestion(
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
            DisplaySetIncorrectQuestion.objects.bulk_create(incorrect_questions)

            # Calculate the success rate
            success_rate = (correct_count / total_questions) * 100 if total_questions > 0 else 0

            subject_id = display_set.subject_id if hasattr(display_set, 'subject') else None

            # Get motivational message
            motivational_message = get_motivational_message(success_rate, subject_id)

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

def get_motivational_message(success_rate, subject_id=None):
    # Determine the range
    range_id = 1  # Default to 0-20%
    if success_rate > 80:
        range_id = 5
    elif success_rate > 60:
        range_id = 4
    elif success_rate > 40:
        range_id = 3
    elif success_rate > 20:
        range_id = 2
   
    # Try to get subject-specific message
    messages = MotivationalMessage.objects.filter(
        success_rate_range=range_id,
        is_active=True
    )
   
    # Check if multiple subjects are involved
    is_multi_subject = False
    if isinstance(subject_id, list) and len(subject_id) > 1:
        is_multi_subject = True
   
    if is_multi_subject:
        # Use multi-subject messages
        multi_messages = MultiSubjectMotivationalMessage.objects.filter(
            success_rate_range=range_id,
            is_active=True
        )
        if multi_messages.exists():
            return multi_messages.order_by('?').first().message
    elif subject_id and not isinstance(subject_id, list):
        subject_messages = messages.filter(subject_id=subject_id)
        if subject_messages.exists():
            return subject_messages.order_by('?').first().message
   
    # Fallback to general message
    general_messages = messages.filter(subject__isnull=True)
    if general_messages.exists():
        return general_messages.order_by('?').first().message
   
    return "İyi çalışmalar!"
