from serializers.quiz_serializers import IncorrectQuestionSerializer
from pagination.custom_pagination import CustomPagination
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from quizzes.models import IncorrectQuestion
from utils.api_responses import ApiResponse
from quizzes.models import Subject, Topic
from rest_framework.views import APIView

class IncorrectQuestionsListView(generics.ListAPIView):
    serializer_class = IncorrectQuestionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = IncorrectQuestion.objects.filter(user=user)

        subject_id = self.request.query_params.get('subject_id')
        topic_id = self.request.query_params.get('topic_id')

        if subject_id:
            queryset = queryset.filter(question__subject_id=subject_id)
        if topic_id:
            queryset = queryset.filter(question__topic_id=topic_id)
        
        return queryset

class IncorrectQuestionsSubjectsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subjects = Subject.objects.filter(
            questions__incorrect_attempts__user=user
        ).distinct()

        subject_data = [
            {'id': subject.id, 'name': subject.name} for subject in subjects
        ]

        return ApiResponse.Success(message="Yanlış soruların olduğu dersler başarıyla getirildi.", data=subject_data)

class IncorrectQuestionsTopicsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_id):
        user = request.user
        topics = Topic.objects.filter(
            questions__incorrect_attempts__user=user,
            subject_id=subject_id
        ).distinct()

        topic_data = [
            {'id': topic.id, 'name': topic.name} for topic in topics
        ]

        return ApiResponse.Success(message="Favori soruların olduğu konular başarıyla getirildi.", data=topic_data)

class DeleteIncorrectQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        user = request.user
        
        try:
            incorrect_question = IncorrectQuestion.objects.get(pk=pk, user=user)
            incorrect_question.delete()
            return ApiResponse.Success(message="Yanlış soru başarıyla silindi.")
        except IncorrectQuestion.DoesNotExist:
            return ApiResponse.NotFound(message="Yanlış soru bulunamadı.")
