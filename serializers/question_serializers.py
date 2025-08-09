from rest_framework import serializers
from questions.models import ExamYear, ExamType, Subject, Topic, Question
from reports.models import QuestionReport, ReportType

class ExamYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamYear
        fields = ['id', 'year']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class ExamTypeSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)

    class Meta:
        model = ExamType
        fields = ['id', 'name', 'subjects']

class SimpleExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = ['id', 'name']

class SubjectWithExamTypeSerializer(serializers.ModelSerializer):
    exam_types = ExamTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'exam_types']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'achievement_code']

class SimpleTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name']

class ReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportType
        fields = ['id', 'name']

class QuestionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionReport
        fields = ['id', 'question', 'report_type', 'report_detail', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        validated_data['user'] = user
        return super().create(validated_data)

class QuestionDetailSerializer(serializers.ModelSerializer):
    exam_year = serializers.SerializerMethodField()
    exam_type = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'question_number', 'correct_answer', 'difficulty_level', 
                  'image_url', 'video_solution_url', 'exam_year', 'exam_type', 
                  'subject', 'topic']
    
    def get_exam_year(self, obj):
        if obj.exam_year:
            return {
                'id': obj.exam_year.id,
                'year': obj.exam_year.year
            }
        return None
    
    def get_exam_type(self, obj):
        if obj.exam_type:
            return {
                'id': obj.exam_type.id,
                'name': obj.exam_type.name
            }
        return None
    
    def get_subject(self, obj):
        if obj.subject:
            return {
                'id': obj.subject.id,
                'name': obj.subject.name
            }
        return None
    
    def get_topic(self, obj):
        if obj.topic:
            return {
                'id': obj.topic.id,
                'name': obj.topic.name,
                'achievement_code': obj.topic.achievement_code
            }
        return None
