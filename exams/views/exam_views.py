from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from exams.models import Exam
from utils.api_responses import ApiResponse
from serializers.exam_serializers import ExamSerializer, UserExamSelectionSerializer

class ExamAPIView(APIView):
    permission_classes = [IsAuthenticated]

    '''
    For GET method, we display selected exams by the user if there are any, otherwise we display 
    exams that are set to be displayed in the homepage in the admin panel by 'display_in_homepage' field.
    '''

    def get(self, request):
        try:
            exams = Exam.objects.all()
            serializer = ExamSerializer(exams, many=True)

            # Fetch user's selected exams
            user = request.user
            selected_exams = user.exams.all()

            # Determine homepage exams
            if selected_exams.exists():
                homepage_exams = selected_exams
            else:
                homepage_exams = Exam.objects.filter(display_in_homepage=True)

            homepage_exam_serializer = ExamSerializer(homepage_exams, many=True)

            return ApiResponse.Success(data={
                "homepage": homepage_exam_serializer.data,
                "all_exams": serializer.data
            })

        except Exception as e:
            return ApiResponse.InternalServerError(message="Sınavlar getirilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

class ExamSelectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = UserExamSelectionSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return ApiResponse.Success(message="Sınavlar başarıyla seçildi.", data=serializer.data)
        return ApiResponse.BadRequest("Geçersiz sınavlar seçildi.")

    def get(self, request):
        user = request.user
        serializer = UserExamSelectionSerializer(user)
        exam_ids = serializer.data['exams']
        exams = Exam.objects.filter(id__in=exam_ids)
        exam_serializer = ExamSerializer(exams, many=True)
        return ApiResponse.Success(data={"exams": exam_serializer.data})
