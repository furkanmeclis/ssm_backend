from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from quizzes.models import FavoriteQuestion, Question, QuizAttempt, Subject, Topic
from serializers.quiz_serializers import FavoriteQuestionSerializer
from utils.api_responses import ApiResponse
from pagination.custom_pagination import CustomPagination

class ToggleFavoriteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        question_id = request.data.get('question_id')
        quiz_attempt_id = request.data.get('quiz_attempt_id', None)

        if not question_id:
            return ApiResponse.BadRequest("question_id zorunludur.")

        try:
            question_id = int(question_id)
        except ValueError:
            return ApiResponse.BadRequest("Geçersiz question_id formatı.")

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return ApiResponse.NotFound("Soru bulunamadı.")

        # Check if the question is already favorited
        try:
            favorite = FavoriteQuestion.objects.get(
                user=user,
                question=question
            )
            # If it exists, remove it (unfavorite)
            favorite.delete()
            return ApiResponse.Success("Soru favorilerden kaldırıldı.", data={"favorited": False})

        except FavoriteQuestion.DoesNotExist: # If it does not exist, add it as a favorite
            # Fetch the questions in the quiz and find the index (order) of the specific question
            if not quiz_attempt_id:
                return ApiResponse.BadRequest("quiz_attempt_id favori eklemek için zorunludur.")
            try:
                quiz_attempt = QuizAttempt.objects.get(id=quiz_attempt_id, user=user)
            except QuizAttempt.DoesNotExist:
                return ApiResponse.NotFound("Sınav denemesi bulunamadı.")
            
            if not quiz_attempt.details['answers'] or not any(
                ans['question_id'] == question_id for ans in quiz_attempt.details['answers']
            ):
                return ApiResponse.BadRequest("Soru bu sınava ait değildir.")

            questions = quiz_attempt.quiz.questions.all().values_list('id', flat=True)
            try:
                question_order = list(questions).index(question_id) + 1
            except ValueError:
                return ApiResponse.BadRequest("Soru sınavda bulunamadı.")

            favorite = FavoriteQuestion.objects.create(
                user=user,
                question=question,
                quiz=quiz_attempt.quiz,
                quiz_attempt=quiz_attempt,
                question_order=question_order
            )
            return ApiResponse.Success("Soru başarıyla favorilere eklendi.", data={"favorited": True})

class FavoriteQuestionsListView(generics.ListAPIView):
    serializer_class = FavoriteQuestionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = FavoriteQuestion.objects.filter(user=user)
        
        subject_id = self.request.query_params.get('subject_id')
        topic_id = self.request.query_params.get('topic_id')

        if subject_id:
            queryset = queryset.filter(question__subject_id=subject_id)
        if topic_id:
            queryset = queryset.filter(question__topic_id=topic_id)

        return queryset

class FavoriteSubjectsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subjects = Subject.objects.filter(
            questions__favorited_by__user=user
        ).distinct()

        subject_data = [
            {'id': subject.id, 'name': subject.name} for subject in subjects
        ]

        return ApiResponse.Success(message="Favori soruların olduğu dersler başarıyla getirildi.", data=subject_data)

class FavoriteTopicsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_id):
        user = request.user
        topics = Topic.objects.filter(
            questions__favorited_by__user=user,
            subject_id=subject_id
        ).distinct()

        topic_data = [
            {'id': topic.id, 'name': topic.name} for topic in topics
        ]

        return ApiResponse.Success(message="Favori soruların olduğu konular başarıyla getirildi.", data=topic_data)
