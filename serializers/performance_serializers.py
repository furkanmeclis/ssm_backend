from rest_framework import serializers
from performance_metrics.models import SubjectPerformance

class SubjectPerformanceSerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SubjectPerformance
        fields = ('id', 'subject', 'subject_name', 'correct_count', 'incorrect_count', 
                  'unanswered_count', 'unseen_count', 'total_questions', 'success_rate',
                  'correct_percentage', 'incorrect_percentage', 'unanswered_percentage',
                  'unseen_percentage', 'updated_at')
    
    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None
