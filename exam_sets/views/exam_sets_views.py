from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from exam_sets.models import ExamSet, UserExamConfiguration, ExamSetQuiz, ExamSetQuizGroup, ExamSetDisplaySet
from quizzes.models import QuizGroup, Quiz, QuestionDisplaySet
from questions.models import Question
from serializers.exam_set_serializers import ExamSetSerializer, UserExamConfigurationSerializer, DetailedUserExamConfigurationSerializer, ExamSetDisplaySetSerializer, SimpleExamSetQuizGroupSerializer, DetailedExamSetQuizSerializer, DetailedExamSetDisplaySetSerializer
from serializers.quiz_serializers import SimpleQuizGroupSerializer, QuestionDisplaySetSerializer
from utils.api_responses import ApiResponse
from pagination.custom_pagination import CustomPagination
from rest_framework.exceptions import ValidationError, NotFound as DRFNotFound
from django.http import Http404
from serializers.question_serializers import QuestionDetailSerializer
import random

class ExamSetViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            return None
    
    def get_queryset(self):
        return ExamSet.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExamSetSerializer
        return ExamSetSerializer
    
    @action(detail=True, methods=['post'])
    def create_quiz(self, request, pk=None):
        exam_set = self.get_object()
        if exam_set is None:
            return ApiResponse.NotFound(message="Bu sınav seti bulunamadı.")
            
        quiz_name = request.data.get('name')
        
        if not quiz_name:
            return ApiResponse.BadRequest(message="Test ismi gereklidir.")
        
        # Check if quiz group already exists
        existing_quiz_group = ExamSetQuizGroup.objects.filter(
            name=quiz_name,
            created_by=request.user,
            exam_set=exam_set
        ).first()
        
        if existing_quiz_group:
            serializer = SimpleExamSetQuizGroupSerializer(existing_quiz_group, context={'request': request})
            return ApiResponse.Success(data=serializer.data)
        
        # Create exam set quiz group
        quiz_group = ExamSetQuizGroup.objects.create(
            name=quiz_name,
            created_by=request.user,
            exam_set=exam_set
        )
        
        # Set relationships
        if exam_set.exam_years.exists():
            quiz_group.exam_years.set(exam_set.exam_years.all())
            
        if exam_set.exam_types.exists():
            quiz_group.exam_types.set(exam_set.exam_types.all())
            
        if exam_set.ordered_subjects.exists():
            quiz_group.subjects.set(exam_set.ordered_subjects.all())
            
        if exam_set.topics.exists():
            quiz_group.topic.set(exam_set.topics.all())
        
        # Get ordered subjects with their order
        ordered_subject_ids = []
        if exam_set:
            ordered_subjects = exam_set.examsetsubject_set.all().order_by('order')
            ordered_subject_ids = [item.subject_id for item in ordered_subjects]
        
        # Get all questions that match criteria
        all_questions = []
        
        if ordered_subject_ids:
            # Get questions by subject order
            for subject_id in ordered_subject_ids:
                subject_query = Question.objects.filter(
                    image_url__isnull=False,
                    subject_id=subject_id
                )
                
                if exam_set.exam_years.exists():
                    subject_query = subject_query.filter(exam_year__in=exam_set.exam_years.all())
                    
                if exam_set.exam_types.exists():
                    subject_query = subject_query.filter(exam_type__in=exam_set.exam_types.all())
                    
                if exam_set.topics.exists():
                    subject_query = subject_query.filter(topic__in=exam_set.topics.all())
                
                # Add questions for this subject ordered by question_number
                subject_questions = list(subject_query.order_by('question_number'))
                all_questions.extend(subject_questions)
        else:
            # No subject ordering, just filter
            query = Question.objects.filter(image_url__isnull=False)
            
            if exam_set.exam_years.exists():
                query = query.filter(exam_year__in=exam_set.exam_years.all())
                
            if exam_set.exam_types.exists():
                query = query.filter(exam_type__in=exam_set.exam_types.all())
                
            if exam_set.ordered_subjects.exists():
                query = query.filter(subject__in=exam_set.ordered_subjects.all())
                
            if exam_set.topics.exists():
                query = query.filter(topic__in=exam_set.topics.all())
            
            all_questions = list(query.order_by('subject', 'question_number'))
        
        if not all_questions:
            return ApiResponse.BadRequest(message="Bu kriterlere uygun soru bulunamadı.")
        
        # Create a single quiz with all questions
        quiz = ExamSetQuiz.objects.create(quiz_group=quiz_group)
        quiz.questions.set(all_questions)
        
        serializer = SimpleExamSetQuizGroupSerializer(quiz_group, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def create_display_set(self, request, pk=None):
        exam_set = self.get_object()
        if exam_set is None:
            return ApiResponse.NotFound(message="Bu sınav seti bulunamadı.")
            
        display_name = request.data.get('name')
        
        if not display_name:
            return ApiResponse.BadRequest(message="PDF ismi gereklidir.")
        
        # Check if display set already exists
        existing_display_set = ExamSetDisplaySet.objects.filter(
            name=display_name,
            created_by=request.user,
            exam_set=exam_set
        ).first()
        
        if existing_display_set:
            serializer = ExamSetDisplaySetSerializer(existing_display_set, context={'request': request})
            return ApiResponse.Success(data=serializer.data)
        
        # Add this line to initialize query
        query = Question.objects.filter(image_url__isnull=False)
        
        if exam_set.exam_years.exists():
            query = query.filter(exam_year__in=exam_set.exam_years.all())
            
        if exam_set.exam_types.exists():
            query = query.filter(exam_type__in=exam_set.exam_types.all())
            
        if exam_set.ordered_subjects.exists():
            query = query.filter(subject__in=exam_set.ordered_subjects.all())
            
        if exam_set.topics.exists():
            query = query.filter(topic__in=exam_set.topics.all())
        
        questions = list(query)
        
        if not questions:
            return ApiResponse.BadRequest(message="Bu kriterlere uygun soru bulunamadı.")
        
        # Create display set
        display_set = ExamSetDisplaySet.objects.create(
            name=display_name,
            created_by=request.user,
            exam_set=exam_set
        )
        
        # Set relationships
        if exam_set.exam_years.exists():
            display_set.exam_years.set(exam_set.exam_years.all())
            
        if exam_set.exam_types.exists():
            display_set.exam_types.set(exam_set.exam_types.all())
            
        if exam_set.ordered_subjects.exists():
            display_set.subjects.set(exam_set.ordered_subjects.all())
            
        if exam_set.topics.exists():
            display_set.topic.set(exam_set.topics.all())
        
        # Get questions in order by subject then question_number
        questions = []
        
        if exam_set.ordered_subjects.exists():
            for subject in exam_set.ordered_subjects.all():
                # Build query for each subject
                subject_query = Question.objects.filter(
                    image_url__isnull=False,
                    subject=subject
                )
                
                if exam_set.exam_years.exists():
                    subject_query = subject_query.filter(exam_year__in=exam_set.exam_years.all())
                    
                if exam_set.exam_types.exists():
                    subject_query = subject_query.filter(exam_type__in=exam_set.exam_types.all())
                    
                if exam_set.topics.exists():
                    subject_query = subject_query.filter(topic__in=exam_set.topics.all())
                
                # Get questions ordered by question_number
                subject_questions = list(subject_query.order_by('question_number'))
                questions.extend(subject_questions)
        else:
            # If no ordered subjects, just get all questions
            query = Question.objects.filter(image_url__isnull=False)
            
            if exam_set.exam_years.exists():
                query = query.filter(exam_year__in=exam_set.exam_years.all())
                
            if exam_set.exam_types.exists():
                query = query.filter(exam_type__in=exam_set.exam_types.all())
                
            if exam_set.topics.exists():
                query = query.filter(topic__in=exam_set.topics.all())
            
            questions = list(query.order_by('question_number'))
        
        if not questions:
            return ApiResponse.BadRequest(message="Bu kriterlere uygun soru bulunamadı.")
        
        display_set.questions.set(questions)
        
        serializer = ExamSetDisplaySetSerializer(display_set, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

    @action(detail=False, methods=['get'], url_path='exam-set-quizzes')
    def exam_set_quizzes(self, request):
        queryset = ExamSetQuizGroup.objects.filter(created_by=request.user)
        page = self.paginate_queryset(queryset)
        
        serializer = SimpleExamSetQuizGroupSerializer(page if page is not None else queryset, many=True, context={'request': request})
        
        if page is not None:
            paginated_response = self.get_paginated_response(serializer.data)
            if isinstance(paginated_response, Response):
                return ApiResponse.Success(data=paginated_response.data, message="Sınav test grupları listelendi.")
            else:
                return ApiResponse.Success(data=paginated_response, message="Sınav test grupları listelendi.")
                
        return ApiResponse.Success(data=serializer.data, message="Sınav test grupları listelendi.")

    @action(detail=False, methods=['get'], url_path='exam-set-quiz/(?P<quiz_id>[^/.]+)')
    def exam_set_quiz_detail(self, request, quiz_id=None):
        try:
            quiz = ExamSetQuiz.objects.get(id=quiz_id, quiz_group__created_by=request.user)
        except ExamSetQuiz.DoesNotExist:
            return ApiResponse.NotFound(message="Test bulunamadı.")
        
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
        
        ordered_questions = sorted(all_questions, key=sort_key)
        
        # Use a custom serializer context to pass the ordered questions
        serializer = DetailedExamSetQuizSerializer(quiz, context={
            'request': request,
            'ordered_questions': ordered_questions
        })
        
        data = serializer.data
        # Replace the questions data with ordered question data
        data['questions'] = [
            QuestionDetailSerializer(q, context={'request': request}).data 
            for q in ordered_questions
        ]
        
        return ApiResponse.Success(data=data, message="Test detayları getirildi.")

    @action(detail=False, methods=['get'], url_path='exam-set-display-sets')
    def exam_set_display_sets(self, request):
        queryset = ExamSetDisplaySet.objects.filter(created_by=request.user)
        page = self.paginate_queryset(queryset)
        
        serializer = ExamSetDisplaySetSerializer(page if page is not None else queryset, many=True, context={'request': request})
        
        if page is not None:
            paginated_response = self.get_paginated_response(serializer.data)
            if isinstance(paginated_response, Response):
                return ApiResponse.Success(data=paginated_response.data, message="Sınav PDF'leri listelendi.")
            else:
                return ApiResponse.Success(data=paginated_response, message="Sınav PDF'leri listelendi.")
                
        return ApiResponse.Success(data=serializer.data, message="Sınav PDF'leri listelendi.")

    @action(detail=False, methods=['get'], url_path='exam-set-display-set/(?P<display_set_id>[^/.]+)')
    def exam_set_display_set_detail(self, request, display_set_id=None):
        try:
            display_set = ExamSetDisplaySet.objects.get(id=display_set_id, created_by=request.user)
        except ExamSetDisplaySet.DoesNotExist:
            return ApiResponse.NotFound(message="PDF bulunamadı.")
        
        # Get the ordered subjects with their order
        ordered_subject_ids = []
        if display_set.exam_set:
            # Get subjects with their order from ExamSetSubject model
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
        
        ordered_questions = sorted(all_questions, key=sort_key)
        
        # Paginate the questions
        page = self.paginate_queryset(ordered_questions)
        
        # Calculate the starting index for the current page
        page_number = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', self.pagination_class.page_size))
        start_index = (page_number - 1) * page_size
        
        # Prepare serialized data with correct question_order
        serialized_questions = []
        for idx, question in enumerate(page, start=start_index + 1):
            question_data = QuestionDetailSerializer(question, context={'request': request}).data
            question_data['question_order'] = idx
            serialized_questions.append(question_data)
        
        # Serialize the display set without the questions first
        display_set_data = DetailedExamSetDisplaySetSerializer(display_set, context={'request': request}).data
        
        # Replace the questions with our paginated and ordered questions
        display_set_data['questions'] = serialized_questions
        
        # Return paginated response
        return self.get_paginated_response(display_set_data)

class UserExamConfigurationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        # Prefetch related objects to optimize detailed serialization
        return UserExamConfiguration.objects.filter(
            created_by=self.request.user, is_active=True
        ).prefetch_related(
            'exam_years', 'exam_types', 'subjects', 'topics'
        )

    def get_serializer_class(self):
        # Use PK-based serializer for write operations (validation/saving)
        if self.action in ['create', 'update', 'partial_update']:
            return UserExamConfigurationSerializer
        # Use Detailed serializer for read operations (responses)
        return DetailedUserExamConfigurationSerializer

    def create(self, request, *args, **kwargs):
        # Use write serializer for input validation and saving
        write_serializer = self.get_serializer(data=request.data)
        try:
            write_serializer.is_valid(raise_exception=True)
            # Manually set creator and active status before saving
            instance = write_serializer.save(created_by=self.request.user, is_active=True)

            # Use detailed serializer for the response
            read_serializer = DetailedUserExamConfigurationSerializer(instance, context={'request': request})
            return ApiResponse.Success(
                data=read_serializer.data,
                message="Sınav setleri başarıyla oluşturuldu.",
            )
        except ValidationError as e:
            return ApiResponse.BadRequest(
                message=e.detail,
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        # Use detailed serializer for response (handled by get_serializer_class)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)

        if page is not None:
            paginated_response = self.get_paginated_response(serializer.data)
            if isinstance(paginated_response, Response):
                return ApiResponse.Success(data=paginated_response.data, message="Sınav setleri listelendi.")
            else:
                return ApiResponse.Success(data=paginated_response, message="Sınav setleri listelendi.")

        return ApiResponse.Success(data=serializer.data, message="Sınav setleri listelendi.")

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Use detailed serializer for response (handled by get_serializer_class)
            serializer = self.get_serializer(instance)
            return ApiResponse.Success(data=serializer.data, message="Sınav setleri detayları getirildi.")
        except (DRFNotFound, Http404):
            return ApiResponse.NotFound(message="Sınav setleri bulunamadı.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
            # Use write serializer for input validation and saving
            write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
            write_serializer.is_valid(raise_exception=True)
            updated_instance = write_serializer.save()

            if getattr(updated_instance, '_prefetched_objects_cache', None):
                updated_instance._prefetched_objects_cache = {}

            # Use detailed serializer for the response
            read_serializer = DetailedUserExamConfigurationSerializer(updated_instance, context={'request': request})
            return ApiResponse.Success(data=read_serializer.data, message="Sınav setleri başarıyla güncellendi.")
        except ValidationError as e:
            return ApiResponse.BadRequest(message=e.detail)
        except (DRFNotFound, Http404):
            return ApiResponse.NotFound(message="Sınav setleri bulunamadı.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return ApiResponse.Success(message="Sınav setleri başarıyla silindi.")
        except (DRFNotFound, Http404):
            return ApiResponse.NotFound(message="Sınav setleri bulunamadı.")


    @action(detail=True, methods=['post'])
    def create_quiz(self, request, pk=None):
        try:
            config = self.get_object()
        except (DRFNotFound, Http404):
            return ApiResponse.NotFound(message="Sınav setleri bulunamadı.")

        quiz_name = request.data.get('name')
        if not quiz_name:
            return ApiResponse.BadRequest(message="Test ismi gereklidir.")

        query = Question.objects.filter(image_url__isnull=False)
        if config.exam_years.exists(): query = query.filter(exam_year__in=config.exam_years.all())
        if config.exam_types.exists(): query = query.filter(exam_type__in=config.exam_types.all())
        if config.subjects.exists(): query = query.filter(subject=config.subjects.first())
        if config.topics.exists(): query = query.filter(topic__in=config.topics.all())

        questions = list(query.distinct())
        if not questions:
            return ApiResponse.BadRequest(message="Bu kriterlere uygun soru bulunamadı.")

        random.shuffle(questions)

        try:
            quiz_group = QuizGroup.objects.create(name=quiz_name, created_by=request.user)
            if config.exam_years.exists(): quiz_group.exam_years.set(config.exam_years.all())
            if config.exam_types.exists(): quiz_group.exam_types.set(config.exam_types.all())
            if config.subjects.exists():
                quiz_group.subject = config.subjects.first()
                quiz_group.save() 
            if config.topics.exists(): quiz_group.topic.set(config.topics.all())

            quiz = Quiz.objects.create(quiz_group=quiz_group)
            quiz.questions.set(questions)

            serializer = SimpleQuizGroupSerializer(quiz_group, context={'request': request})
            return ApiResponse.Success(data=serializer.data, message="Test başarıyla oluşturuldu.")
        except Exception as e:
            return ApiResponse.BadRequest(message=f"Test oluşturulurken hata oluştu: {str(e)}")


    @action(detail=True, methods=['post'])
    def create_display_set(self, request, pk=None):
        try:
            config = self.get_object()
        except (DRFNotFound, Http404):
            return ApiResponse.NotFound(message="Sınav setleri bulunamadı.")

        display_name = request.data.get('name')
        if not display_name:
            return ApiResponse.BadRequest(message="PDF ismi gereklidir.")

        query = Question.objects.filter(image_url__isnull=False)
        if config.exam_years.exists(): query = query.filter(exam_year__in=config.exam_years.all())
        if config.exam_types.exists(): query = query.filter(exam_type__in=config.exam_types.all())
        if config.subjects.exists(): query = query.filter(subject=config.subjects.first())
        if config.topics.exists(): query = query.filter(topic__in=config.topics.all())

        questions = list(query.distinct())
        if not questions:
            return ApiResponse.BadRequest(message="Bu kriterlere uygun soru bulunamadı.")

        try:
            display_set = QuestionDisplaySet.objects.create(name=display_name, created_by=request.user)
            if config.exam_years.exists(): display_set.exam_years.set(config.exam_years.all())
            if config.exam_types.exists(): display_set.exam_types.set(config.exam_types.all())
            if config.subjects.exists():
                display_set.subject = config.subjects.first()
                display_set.save()
            if config.topics.exists(): display_set.topic.set(config.topics.all())

            display_set.questions.set(questions)

            serializer = QuestionDisplaySetSerializer(display_set, context={'request': request})
            return ApiResponse.Success(data=serializer.data, message="PDF başarıyla oluşturuldu.")
        except Exception as e:
            return ApiResponse.BadRequest(message=f"PDF oluşturulurken hata oluştu: {str(e)}")