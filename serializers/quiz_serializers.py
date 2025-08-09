from rest_framework import serializers
from quizzes.models import QuizGroup, Quiz, QuizAttempt, IncorrectQuestion, FavoriteQuestion, QuestionDisplaySet
from questions.models import Question
from serializers.question_serializers import SimpleExamTypeSerializer, ExamYearSerializer, SubjectSerializer, SimpleTopicSerializer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id']

class QuestionDetailSerializer(serializers.ModelSerializer):
    exam_year = ExamYearSerializer(read_only=True)
    exam_type = SimpleExamTypeSerializer(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'correct_answer', 'difficulty_level', 'image_url', 'video_solution_url', 'exam_year', 'exam_type']

class QuestionFullDetailSerializer(serializers.ModelSerializer):
    exam_year = ExamYearSerializer(read_only=True)
    exam_type = SimpleExamTypeSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    topic = SimpleTopicSerializer(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'correct_answer', 'difficulty_level', 'image_url', 'video_solution_url', 'exam_year', 'exam_type', 'subject', 'topic']

class QuizSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'total_questions']

    def get_total_questions(self, obj):
        return obj.questions.count()

class DetailedQuizSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)
    exam_years = ExamYearSerializer(many=True, read_only=True, source='quiz_group.exam_years')
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True, source='quiz_group.exam_types')
    subject = SubjectSerializer(read_only=True, source='quiz_group.subject')
    topic = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'created_at', 'exam_years', 'exam_types', 'subject', 'topic', 'questions']

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
        # Return None if quiz_group is None or has no topics
        return None

class MediumQuizSerializer(serializers.ModelSerializer):
    exam_years = ExamYearSerializer(many=True, read_only=True, source='quiz_group.exam_years')
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True, source='quiz_group.exam_types')
    subject = SubjectSerializer(read_only=True, source='quiz_group.subject')
    topic = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'created_at', 'exam_years', 'exam_types', 'subject', 'topic']

    def get_topic(self, obj):
        # Add a check here:
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
        # Return None if quiz_group is None or has no topics
        return None

class DetailedQuizGroupSerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    topic = serializers.SerializerMethodField()

    class Meta:
        model = QuizGroup
        fields = ['id', 'name', 'exam_years', 'exam_types', 'subject', 'topic', 'created_at', 'quizzes']

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

class SimpleQuizGroupSerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)

    class Meta:
        model = QuizGroup
        fields = ['id', 'name', 'quizzes']

class QuizAttemptSummarySerializer(serializers.ModelSerializer):
    quiz_details = MediumQuizSerializer(source='quiz', read_only=True)
    motivational_message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz_details', 'success_rate', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'success_rate', 'details', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

class DetailedQuizAttemptSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)
    exam_years = serializers.SerializerMethodField()
    exam_types = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'exam_years', 'exam_types', 'subject', 'topic', 'success_rate', 'details', 'correct_count', 'incorrect_count', 'unanswered_count', 'motivational_message', 'created_at']

    def get_exam_years(self, obj):
        return ExamYearSerializer(obj.quiz.quiz_group.exam_years.all(), many=True).data

    def get_exam_types(self, obj):
        return SimpleExamTypeSerializer(obj.quiz.quiz_group.exam_types.all(), many=True).data

    def get_subject(self, obj):
        return SubjectSerializer(obj.quiz.quiz_group.subject).data

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

class IncorrectQuestionSerializer(serializers.ModelSerializer):
    question = QuestionDetailSerializer(read_only=True)
    quiz_attempt = QuizAttemptSummarySerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = IncorrectQuestion
        fields = ['id', 'question', 'user_answer', 'correct_answer', 'user_time', 'quiz_attempt', 'question_order', 'is_favorite']

    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return FavoriteQuestion.objects.filter(user=user, question=obj.question).exists()

class FavoriteQuestionSerializer(serializers.ModelSerializer):
    question = QuestionFullDetailSerializer(read_only=True)

    class Meta:
        model = FavoriteQuestion
        fields = ['id', 'question', 'question_order', 'created_at']

class QuestionDisplaySetSerializer(serializers.ModelSerializer):
    questions = QuestionDetailSerializer(many=True, read_only=True)
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    topic = serializers.SerializerMethodField()

    class Meta:
        model = QuestionDisplaySet
        fields = ['id', 'name', 'exam_years', 'exam_types', 'subject', 'topic', 'questions', 'created_at']

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

class SimpleQuestionDisplaySetSerializer(serializers.ModelSerializer):
    exam_years = ExamYearSerializer(many=True, read_only=True)
    exam_types = SimpleExamTypeSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    topic = serializers.SerializerMethodField()

    class Meta:
        model = QuestionDisplaySet
        fields = ['id', 'name', 'exam_years', 'exam_types', 'subject', 'topic', 'created_at']

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

class QuizGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizGroup
        fields = ['id', 'name', 'created_at']
