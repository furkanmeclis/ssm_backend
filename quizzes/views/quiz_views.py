from rest_framework.views import APIView
from questions.models import Question
from quizzes.models import QuizGroup, Quiz
from serializers.quiz_serializers import DetailedQuizGroupSerializer
from utils.api_responses import ApiResponse
from validations.quiz_validate import validate_quiz_input
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from serializers.quiz_serializers import SimpleQuizGroupSerializer, DetailedQuizSerializer
from pagination.custom_pagination import CustomPagination
import random

class CreateQuizzes(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        year_ids = data.get('year_ids')
        type_ids = data.get('type_ids')
        subject_id = data.get('subject_id')
        topic_id = data.get('topic_id')
        quiz_group_name = data.get('name')
        user = request.user

        try:
            validate_quiz_input(year_ids, type_ids, subject_id, topic_id, quiz_group_name)
        except ValidationError as e:
            return ApiResponse.BadRequest(message=e.detail)

        # Filter questions based on the provided criteria
        questions = Question.objects.filter(
            exam_year__id__in=year_ids,
            exam_type__id__in=type_ids,
            subject__id=subject_id,
            topic__id=topic_id,
            image_url__isnull=False
        )

        question_count = questions.count()

        if question_count == 0:
            return ApiResponse.BadRequest(message="Verilen kriterlere uygun soru bulunamadı.")

        max_questions_per_quiz = 10000000 # Changed from '40' to '10000000' because the limit has been removed
        num_quizzes = (question_count // max_questions_per_quiz) + (1 if question_count % max_questions_per_quiz != 0 else 0)

        quiz_group = QuizGroup.objects.create(name=quiz_group_name, created_by=user, subject_id=subject_id)
        quiz_group.exam_years.set(year_ids)
        quiz_group.exam_types.set(type_ids)
        quiz_group.topic.set([topic_id])

        # Convert queryset to list for easier manipulation
        questions = list(questions)
        random.shuffle(questions)  # Shuffle the list of questions

        # Split questions into quizzes
        questions_per_quiz = question_count // num_quizzes
        extra_questions = question_count % num_quizzes  # Calculate extra questions to distribute

        start_index = 0
        for i in range(num_quizzes):
            # Determine the number of questions for this quiz
            end_index = start_index + questions_per_quiz + (1 if i < extra_questions else 0)
            quiz_questions = questions[start_index:end_index]

            quiz = Quiz.objects.create(quiz_group=quiz_group)
            quiz.questions.set(quiz_questions)
            quiz.save()

            start_index = end_index

        serializer = SimpleQuizGroupSerializer(quiz_group, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class QuizGroupListView(generics.ListAPIView):
    serializer_class = DetailedQuizGroupSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return QuizGroup.objects.filter(created_by=user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response

class QuizGroupDetailView(APIView):
    def get(self, request, pk):
        try:
            quiz_group = QuizGroup.objects.get(pk=pk, created_by=request.user)
            serializer = DetailedQuizGroupSerializer(quiz_group, context={'request': request})
            return ApiResponse.Success(data=serializer.data)
        except QuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav grubu bulunamadı.')

    def delete(self, request, pk):
        try:
            quiz_group = QuizGroup.objects.get(pk=pk, created_by=request.user)
            quiz_group.delete()
            return ApiResponse.Success(message="Sınav grubu başarıyla silindi.")
        except QuizGroup.DoesNotExist:
            return ApiResponse.NotFound(message="Sınav grubu bulunamadı.")

class QuizDetailView(APIView):
    def get(self, request, pk):
        try:
            quiz = Quiz.objects.get(pk=pk, quiz_group__created_by=request.user)
            serializer = DetailedQuizSerializer(quiz, context={'request': request})
            return ApiResponse.Success(data=serializer.data)
        except Quiz.DoesNotExist:
            return ApiResponse.NotFound(message='Sınav bulunamadı.')
        
    def delete(self, request, pk):
        try:
            quiz = Quiz.objects.get(pk=pk, quiz_group__created_by=request.user)
            quiz.delete()
            return ApiResponse.Success(message="Sınav başarıyla silindi.")
        except Quiz.DoesNotExist:
            return ApiResponse.NotFound(message="Sınav bulunamadı.")
