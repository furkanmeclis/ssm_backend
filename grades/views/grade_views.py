from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.api_responses import ApiResponse
from serializers.grade_serializers import GradeLevelSerializer
from grades.models import GradeLevel

class GradeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        grades = [{'id': grade.value, 'name': grade.label} for grade in GradeLevel]
        serializer = GradeLevelSerializer(grades, many=True)
        return ApiResponse.Success(data=serializer.data)

class UserGradeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        grade = user.grade
        grade_data = {
            'id': grade,
            'name': GradeLevel(grade).label if grade else None
        }
        return ApiResponse.Success(data=grade_data)

    def post(self, request):
        user = request.user
        grade_id = request.data.get('grade')
        if grade_id in GradeLevel.values:
            user.grade = grade_id
            user.save()
            return ApiResponse.Success(message="Sınıf başarıyla güncellendi.")
        else:
            return ApiResponse.BadRequest(message="Geçersiz sınıf.")
