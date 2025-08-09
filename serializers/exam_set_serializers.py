from rest_framework import serializers
from questions.models import ExamYear, ExamType, Subject, Topic
from exam_sets.models import ExamSet, UserExamConfiguration, ExamSetQuiz, ExamSetQuizGroup, ExamSetDisplaySet, ExamSetQuizAttempt, ExamSetDisplaySetAttempt
from serializers.quiz_serializers import ExamYearSerializer, SimpleExamTypeSerializer, SubjectSerializer, SimpleTopicSerializer, QuestionDetailSerializer, MediumQuizSerializer
from quizzes.models import FavoriteQuestion, Quiz

class ExamSetSerializer(serializers.ModelSerializer):
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topics = SimpleTopicSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExamSet
        fields = ['id', 'name', 'description', 'exam_years', 'exam_types', 
                 'subjects', 'topics', 'created_at', 'is_active']

class SimpleExamSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSet
        fields = ['id', 'name', 'created_at']

class UserExamConfigurationSerializer(serializers.ModelSerializer):
    exam_years = serializers.PrimaryKeyRelatedField(
      queryset=ExamYear.objects.all(), many=True, required=False,
      error_messages={'does_not_exist': 'Belirtilen Exam Year ID geçerli değil.'}
    )
    exam_types = serializers.PrimaryKeyRelatedField(
      queryset=ExamType.objects.all(), many=True, required=False,
      error_messages={'does_not_exist': 'Belirtilen Exam Type ID geçerli değil.'}
    )
    subjects = serializers.PrimaryKeyRelatedField(
      queryset=Subject.objects.all(), many=True, required=False,
      error_messages={'does_not_exist': 'Belirtilen Subject ID geçerli değil.'}
    )
    topics = serializers.PrimaryKeyRelatedField(
      queryset=Topic.objects.all(), many=True, required=False,
      error_messages={'does_not_exist': 'Belirtilen Topic ID geçerli değil.'}
    )

    class Meta:
        model = UserExamConfiguration
        fields = ['id', 'name', 'description', 'exam_years', 'exam_types',
                  'subjects', 'topics']
        read_only_fields = ['id']

class SimpleUserExamConfigurationSerializer(serializers.ModelSerializer):
  class Meta:
    model = UserExamConfiguration
    fields = ['id', 'name', 'description', 'created_at']

class DetailedUserExamConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for READ operations (list, retrieve, create/update response).
    Displays nested details for relationships.
    """
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topics = SimpleTopicSerializer(many=True, read_only=True)
    creator_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = UserExamConfiguration
        fields = ['id', 'name', 'description', 'exam_years', 'exam_types',
                  'subjects', 'topics', 'created_at', 'is_active', 'creator_username']
        read_only_fields = fields # All fields are read-only in this context

class ExamSetQuizSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = ExamSetQuiz
        fields = ['id', 'total_questions']

    def get_total_questions(self, obj):
        return obj.questions.count()

class SimpleExamSetQuizGroupSerializer(serializers.ModelSerializer):
    quizzes = ExamSetQuizSerializer(many=True, read_only=True)

    class Meta:
        model = ExamSetQuizGroup
        fields = ['id', 'name', 'quizzes']

class ExamSetDisplaySetSerializer(serializers.ModelSerializer):
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()

    class Meta:
        model = ExamSetDisplaySet
        fields = ['id', 'name', 'exam_years', 'exam_types', 'subjects', 'topic', 'created_at']

    def get_topic(self, obj):
        topics = obj.topic.all()
        count = topics.count()
        
        # Check if there's a request parameter to force list format
        request = self.context.get('request')
        force_list = request and request.query_params.get('format_topics') == 'list'
        
        if count == 1 and not force_list:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count >= 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None
    
class DetailedExamSetDisplaySetSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()

    class Meta:
        model = ExamSetDisplaySet
        fields = ['id', 'name', 'exam_years', 'exam_types', 'subjects', 'topic', 'questions', 'created_at']

    def get_topic(self, obj):
        topics = obj.topic.all()
        count = topics.count()
        
        # Check if there's a request parameter to force list format
        request = self.context.get('request')
        force_list = request and request.query_params.get('format_topics') == 'list'
        
        if count == 1 and not force_list:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count >= 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None

class DetailedExamSetQuizSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)
    exam_years = ExamYearSerializer(many=True, read_only=True, source='quiz_group.exam_years')
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True, source='quiz_group.exam_types')
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSetQuiz
        fields = ['id', 'created_at', 'exam_years', 'exam_types', 'subjects', 'topic', 'questions']
 
    def get_topic(self, obj):
        if obj.quiz_group:
            topics = obj.quiz_group.topic.all()
            count = topics.count()
            
            # Check if there's a request parameter to force list format
            request = self.context.get('request')
            force_list = request and request.query_params.get('format_topics') == 'list'
            
            if count == 1 and not force_list:
                return SimpleTopicSerializer(topics.first(), many=False).data
            elif count >= 1:
                return SimpleTopicSerializer(topics, many=True).data
        return None

class MediumExamSetQuizSerializer(serializers.ModelSerializer):
    exam_years = ExamYearSerializer(many=True, read_only=True, source='quiz_group.exam_years')
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True, source='quiz_group.exam_types')
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSetQuiz
        fields = ['id', 'created_at', 'exam_years', 'exam_types', 'subjects', 'topic']
    
    def get_topic(self, obj):
        if not obj.quiz_group:
            return None
        
        topics = obj.quiz_group.topic.all()
        count = topics.count()
    
        # Check if there's a request parameter to force list format
        request = self.context.get('request')
        force_list = request and request.query_params.get('format_topics') == 'list'
        
        if count == 1 and not force_list:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count >= 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None

class ExamSetQuizAttemptSummarySerializer(serializers.ModelSerializer):
    quiz_details = MediumExamSetQuizSerializer(source='quiz', read_only=True)
    motivational_message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = ExamSetQuizAttempt
        fields = ['id', 'quiz_details', 'success_rate', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

    def get_quiz_details(self, obj):
        return {'id': obj.quiz.id, 'name': obj.quiz.quiz_group.name}


class DetailedExamSetQuizAttemptSerializer(serializers.ModelSerializer):
    quiz = serializers.SerializerMethodField()
    exam_years = serializers.SerializerMethodField()
    exam_types = serializers.SerializerMethodField()
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSetQuizAttempt
        fields = ['id', 'quiz', 'exam_years', 'exam_types', 'subjects', 'topic', 'success_rate', 'details', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']  # Changed subject to ordered_subjects
    
    def get_quiz(self, obj):
        return {'id': obj.quiz.id, 'total_questions': obj.quiz.questions.count()}
    
    def get_exam_years(self, obj):
        return ExamYearSerializer(obj.quiz.quiz_group.exam_years.all(), many=True).data
    
    def get_exam_types(self, obj):
        return SimpleExamTypeSerializer(obj.quiz.quiz_group.exam_types.all(), many=True).data
    
    def get_subjects(self, obj):
        if obj.quiz.quiz_group.ordered_subjects.exists():
            return SubjectSerializer(obj.quiz.quiz_group.ordered_subjects.all(), many=True).data
        return []
    
    def get_topic(self, obj):
        topics = obj.quiz.quiz_group.topic.all()
        count = topics.count()
        
        # Check if there's a request parameter to force list format
        request = self.context.get('request')
        force_list = request and request.query_params.get('format_topics') == 'list'
        
        if count == 1 and not force_list:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count >= 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None

    def get_details(self, obj):
        answers = obj.details.get('answers', [])
        user = obj.user

        # Sort the answers by question_order
        answers = sorted(answers, key=lambda x: x.get('question_order', 0))

        for answer in answers:
            question_id = answer.get('question_id')
            is_favorite = FavoriteQuestion.objects.filter(
                user=user,
                question_id=question_id
            ).exists()
            answer['is_favorite'] = is_favorite

        return {
            'answers': answers
        }

class ExamSetDisplaySetAttemptSummarySerializer(serializers.ModelSerializer):
    display_set_details = serializers.SerializerMethodField()
    motivational_message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = ExamSetDisplaySetAttempt
        fields = ['id', 'display_set_details', 'success_rate', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

    def get_display_set_details(self, obj):
        return {
            'id': obj.display_set.id,
            'name': obj.display_set.name,
            'created_at': obj.display_set.created_at,
            'exam_years': ExamYearSerializer(obj.display_set.exam_years.all(), many=True).data,
            'exam_types': SimpleExamTypeSerializer(obj.display_set.exam_types.all(), many=True).data,
            'subject': SubjectSerializer(obj.display_set.ordered_subjects.first()).data if obj.display_set.ordered_subjects.exists() else None,
            'topic': self._get_topics_data(obj.display_set)
        }
    
    def _get_topics_data(self, display_set):
        topics = display_set.topic.all()
        count = topics.count()
        if count == 1:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count > 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None

class DetailedExamSetDisplaySetAttemptSerializer(serializers.ModelSerializer):
    display_set = serializers.SerializerMethodField()
    exam_years = serializers.SerializerMethodField()
    exam_types = serializers.SerializerMethodField()
    subjects = SubjectSerializer(source='ordered_subjects', many=True, read_only=True)
    topic = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()

    class Meta:
        model = ExamSetDisplaySetAttempt
        fields = ['id', 'display_set', 'exam_years', 'exam_types', 'subjects', 'topic', 'success_rate', 'details', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

    def get_display_set(self, obj):
        return {'id': obj.display_set.id, 'name': obj.display_set.name}

    def get_exam_years(self, obj):
        return ExamYearSerializer(obj.display_set.exam_years.all(), many=True).data

    def get_exam_types(self, obj):
        return SimpleExamTypeSerializer(obj.display_set.exam_types.all(), many=True).data

    def get_subjects(self, obj):
        if obj.display_set.ordered_subjects.exists():
            return SubjectSerializer(obj.display_set.ordered_subjects.all(), many=True).data
        return []

    def get_topic(self, obj):
        topics = obj.display_set.topic.all()
        count = topics.count()
        
        # Check if there's a request parameter to force list format
        request = self.context.get('request')
        force_list = request and request.query_params.get('format_topics') == 'list'
        
        if count == 1 and not force_list:
            return SimpleTopicSerializer(topics.first(), many=False).data
        elif count >= 1:
            return SimpleTopicSerializer(topics, many=True).data
        return None

    def get_details(self, obj):
        answers = obj.details.get('answers', [])
        user = obj.user

        # Sort the answers by question_order
        answers = sorted(answers, key=lambda x: x.get('question_order', 0))

        for answer in answers:
            question_id = answer.get('question_id')
            is_favorite = FavoriteQuestion.objects.filter(
                user=user,
                question_id=question_id
            ).exists()
            answer['is_favorite'] = is_favorite

        return {
            'answers': answers
        }
