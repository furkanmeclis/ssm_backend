from utils.api_responses import ApiResponse
from rest_framework.permissions import IsAuthenticated
from quizzes.models import QuestionDisplaySet, QuizGroup
from validations.quiz_validate import validate_quiz_input
from rest_framework.exceptions import ValidationError
from django.db.models import Value as V, CharField
from rest_framework.views import APIView
from questions.models import Question
from rest_framework import viewsets
from pagination.custom_pagination import CustomPagination
from serializers.quiz_serializers import QuestionDisplaySetSerializer, SimpleQuestionDisplaySetSerializer, DetailedQuizGroupSerializer, QuestionDetailSerializer
from itertools import chain
import heapq

class QuestionDisplaySetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    paginator = CustomPagination()

    def list(self, request):
        user = request.user
        question_display_sets = QuestionDisplaySet.objects.filter(created_by=user)
        page = self.paginator.paginate_queryset(question_display_sets, request)
        serializer = SimpleQuestionDisplaySetSerializer(page, many=True, context={'request': request})
        return self.paginator.get_paginated_response(serializer.data)
    
    def retrieve(self, request, pk=None):
        if not pk:
            return ApiResponse.BadRequest(message="Geçersiz id.")

        user = request.user
        question_display_set = QuestionDisplaySet.objects.filter(pk=pk, created_by=user).first()

        if not question_display_set:
            return ApiResponse.NotFound(message="Verilen id'ye uygun soru seti bulunamadı.")

        # Get the related questions
        questions = question_display_set.questions.all().order_by('id')

        # Paginate the questions
        paginated_questions = self.paginator.paginate_queryset(questions, request)
        
        # Calculate the starting index for the current page
        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.paginator.page_size))
        start_index = (page_number - 1) * page_size

        # Prepare serialized data with correct question_order
        serialized_questions = []
        for idx, question in enumerate(paginated_questions, start=start_index + 1):  # Adjust starting index
            question_data = QuestionDetailSerializer(question).data
            question_data['question_order'] = idx  # Add question_order to the serialized data
            serialized_questions.append(question_data)

        # Serialize the display set without the questions
        display_set_serializer = QuestionDisplaySetSerializer(question_display_set, context={'request': request})

        # Combine the display set data with the paginated questions
        data = display_set_serializer.data
        data['questions'] = serialized_questions

        return self.paginator.get_paginated_response(data)

    def create(self, request):
        data = request.data
        year_ids = data.get('year_ids')
        type_ids = data.get('type_ids')
        subject_id = data.get('subject_id')
        topic_id = data.get('topic_id')
        display_set_name = data.get('name')
        user = request.user

        try:
            validate_quiz_input(year_ids, type_ids, subject_id, topic_id, display_set_name)
        except ValidationError as e:
            return ApiResponse.BadRequest(message=e.detail)

        questions = Question.objects.filter(
            exam_year__id__in=year_ids,
            exam_type__id__in=type_ids,
            subject__id=subject_id,
            topic__id=topic_id,
            image_url__isnull=False
        )

        if not questions.exists():
            return ApiResponse.BadRequest(message="Verilen kriterlere uygun soru bulunamadı.")

        question_display_set = QuestionDisplaySet.objects.create(
            name=display_set_name,
            created_by=user,
            subject_id=subject_id,
        )

        question_display_set.exam_years.set(year_ids)
        question_display_set.topic.set([topic_id])
        question_display_set.exam_types.set(type_ids)
        question_display_set.questions.set(questions)

        serializer = QuestionDisplaySetSerializer(question_display_set, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

    def delete(self, request, pk=None):
        if not pk or not pk.isdigit():
            return ApiResponse.BadRequest(message="Geçersiz id.")

        try:
            question_display_set = QuestionDisplaySet.objects.get(pk=pk, created_by=request.user)
            question_display_set.delete()
            return ApiResponse.Success(message="Soru seti başarıyla silindi.")
        except QuestionDisplaySet.DoesNotExist:
            return ApiResponse.NotFound(message="Verilen id'ye uygun soru seti bulunamadı.")

class LatestFourQuizGroupsAndDisplaySetsView(APIView):
    def get(self, request):
        # Fetch the latest 4 items from both QuizGroup and QuestionDisplaySet combined
        latest_quiz_groups = QuizGroup.objects.annotate(type=V('quiz_group', output_field=CharField())).order_by('-created_at')[:4]
        latest_display_sets = QuestionDisplaySet.objects.annotate(type=V('display_set', output_field=CharField())).order_by('-created_at')[:4]

        # Combine the two querysets and order them by created_at to get the latest 4 overall
        combined_results = heapq.nlargest(4, chain(latest_quiz_groups, latest_display_sets), key=lambda x: x.created_at)

        # Serialize the combined results
        serialized_data = []
        for item in combined_results:
            if hasattr(item, 'quizzes'):
                serializer = DetailedQuizGroupSerializer(item, context={'request': request})
                serialized_data.append({'type': 'quiz_group', 'data': serializer.data})
            else:
                serializer = SimpleQuestionDisplaySetSerializer(item, context={'request': request})
                serialized_data.append({'type': 'display_set', 'data': serializer.data})

        return ApiResponse.Success(data=serialized_data)
