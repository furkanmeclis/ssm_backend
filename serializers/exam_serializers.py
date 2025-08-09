from rest_framework import serializers
from exams.models import Exam
from users.models import CustomUser
from ogmmateryal.models import ExamStructure, ExamSection, ExamSubject

class ExamSerializer(serializers.ModelSerializer):
    remaining_days = serializers.SerializerMethodField()
    detailed_remaining_time = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ['id', 'title', 'exam_date', 'remaining_days', 'detailed_remaining_time', 'is_major_exam']

    def get_remaining_days(self, obj):
        remaining_days, _ = obj.calculate_remaining_time()
        return remaining_days if remaining_days is not None else None

    def get_detailed_remaining_time(self, obj):
        _, detailed_remaining_time = obj.calculate_remaining_time()
        return detailed_remaining_time if detailed_remaining_time is not None else "Sınav tarihi geçti"

class ExamSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title', 'exam_date', 'is_major_exam']

class UserExamSelectionSerializer(serializers.ModelSerializer):
    exams = serializers.PrimaryKeyRelatedField(queryset=Exam.objects.all(), many=True)

    class Meta:
        model = CustomUser
        fields = ['exams']

class SimpleExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title']

class ExamSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSubject
        fields = ['id', 'name', 'question_count']

class ExamSectionSerializer(serializers.ModelSerializer):
    subjects = ExamSubjectSerializer(many=True)

    class Meta:
        model = ExamSection
        fields = ['id', 'name', 'subjects']

class ExamStructureSerializer(serializers.ModelSerializer):
    sections = ExamSectionSerializer(many=True)

    class Meta:
        model = ExamStructure
        fields = ['id', 'name', 'sections']

    def to_representation(self, instance):
        """Custom representation to better match the expected JSON structure."""
        representation = super().to_representation(instance)
        return representation
