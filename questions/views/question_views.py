from questions.models import ExamYear, Topic, Subject, ExamType, Question
from serializers.question_serializers import ExamYearSerializer, SimpleExamTypeSerializer, SubjectSerializer, TopicSerializer, QuestionDetailSerializer
from utils.api_responses import ApiResponse
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

class ExamYearList(APIView):
    def get(self, request, *args, **kwargs):
        exam_years = ExamYear.objects.filter(
            questions__isnull=False,
            questions__image_url__isnull=False,
            questions__topic__isnull=False
        ).distinct().order_by('-year')
        serializer = ExamYearSerializer(exam_years, many=True, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class ExamTypeList(APIView):
    def get(self, request, *args, **kwargs):
        year_ids = request.query_params.get('year_ids')
        if not year_ids:
            return ApiResponse.BadRequest(message="year_ids gereklidir.")

        year_ids = year_ids.split(',')

        # Fetch all exam types that have questions in any of the selected years
        exam_types = ExamType.objects.filter(
            questions__exam_year__id__in=year_ids,
            questions__image_url__isnull=False,
            questions__topic__isnull=False
        ).distinct().order_by('name')

        serializer = SimpleExamTypeSerializer(exam_types, many=True, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class SubjectList(APIView):
    def get(self, request, *args, **kwargs):
        year_ids = request.query_params.get('year_ids')
        type_ids = request.query_params.get('type_ids')

        if not year_ids or not type_ids:
            return ApiResponse.BadRequest(message="year_ids ve type_ids gereklidir.")

        year_ids = list(map(int, year_ids.split(',')))
        type_ids = list(map(int, type_ids.split(',')))

        # Fetch all subjects that have questions in any of the selected years and exam types
        subjects = Subject.objects.filter(
            questions__exam_year__id__in=year_ids,
            questions__exam_type__id__in=type_ids,
            questions__topic__isnull=False,
            questions__image_url__isnull=False
        ).distinct().order_by('name')

        serializer = SubjectSerializer(subjects, many=True, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class TopicList(APIView):
    def get(self, request, *args, **kwargs):
        year_ids = request.query_params.get('year_ids')
        type_ids = request.query_params.get('type_ids')
        subject_id = request.query_params.get('subject_id')

        if not year_ids or not type_ids or not subject_id:
            return ApiResponse.BadRequest(message="year_ids, type_ids ve subject_id gereklidir.")

        if not subject_id.isdigit():
            return ApiResponse.BadRequest(message="Tek ders seçilebilir.")

        year_ids = list(map(int, year_ids.split(',')))
        type_ids = list(map(int, type_ids.split(',')))

        # Fetch all topics that have questions in any of the selected years, exam types, and subject
        topics = Topic.objects.filter(
            subject__id=subject_id,
            questions__exam_year__id__in=year_ids,
            questions__exam_type__id__in=type_ids,
            questions__image_url__isnull=False
        ).distinct().order_by('name')

        serializer = TopicSerializer(topics, many=True, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class QuestionCodec:
    # Characters for our encoding (36 chars: 0-9, a-z)
    CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"
    # Simple XOR key
    XOR_KEY = 54321
    
    @classmethod
    def encode(cls, question_id):
        """Convert a question ID to an obfuscated string."""
        # Simple XOR and bit shift
        num = (question_id ^ cls.XOR_KEY) + 10000
        
        # Convert to base-36 string
        result = ""
        while num > 0:
            result = cls.CHARS[num % len(cls.CHARS)] + result
            num //= len(cls.CHARS)
            
        # Ensure minimum length
        if len(result) < 4:
            result = cls.CHARS[0] * (4 - len(result)) + result
            
        return result
    
    @classmethod
    def decode(cls, code_str):
        """Convert an obfuscated string back to a question ID."""
        # Convert from base-36 to number
        num = 0
        for char in code_str:
            if char not in cls.CHARS:
                raise ValueError("Invalid character in code")
            num = num * len(cls.CHARS) + cls.CHARS.index(char)
            
        # Reverse the operations
        return (num - 10000) ^ cls.XOR_KEY

class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request, code):
        try:
            # Decode the question ID from the code
            question_id = QuestionCodec.decode(code)
            question = Question.objects.get(id=question_id)
        except (ValueError, Question.DoesNotExist):
            return ApiResponse.BadRequest(message="Bu soru bulunamadı.")
       
        serializer = QuestionDetailSerializer(question, context={'request': request})
        return ApiResponse.Success(data=serializer.data)
