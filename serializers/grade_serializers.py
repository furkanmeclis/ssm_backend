from rest_framework import serializers
from grades.models import GradeLevel

class GradeLevelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
