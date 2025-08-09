from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from reports.models import QuestionReport, ReportType
from serializers.question_serializers import ReportTypeSerializer, QuestionReportSerializer
from utils.api_responses import ApiResponse
from questions.models import Question
from django.db import IntegrityError

class ReportTypeListView(APIView):
    def get(self, request, *args, **kwargs):
        report_types = ReportType.objects.all()
        serializer = ReportTypeSerializer(report_types, many=True, context={'request': request})
        return ApiResponse.Success(data=serializer.data)

class QuestionReportCreateView(APIView):
    def post(self, request, question_id, *args, **kwargs):
        report_type_id = request.data.get('report_type')
        report_detail = request.data.get('report_detail', None)

        if not report_type_id:
            return ApiResponse.BadRequest(message='Rapor türü belirtilmelidir.')
        try:
            report_type = ReportType.objects.get(id=report_type_id)
        except ReportType.DoesNotExist:
            return ApiResponse.NotFound(message='Rapor türü bulunamadı.')
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return ApiResponse.NotFound(message='Soru bulunamadı.')

        # Combine the request data with the question object
        data = request.data.copy()
        data['question'] = question.id

        serializer = QuestionReportSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save(user=request.user, question=question)
                return ApiResponse.Success("Rapor başarıyla gönderildi.")
            except IntegrityError:
                return ApiResponse.BadRequest(message='Bu soru için bu rapor türünü zaten gönderdiniz.')
        return ApiResponse.BadRequest(message='Geçersiz veri.', data=serializer.errors)

class DeleteReportsView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, question_id, report_type_id=None):
        try:
            if report_type_id:
                # Delete all reports of the specific type for this question
                QuestionReport.objects.filter(
                    question_id=question_id,
                    report_type_id=report_type_id
                ).delete()
            else:
                # Delete all reports for the question
                QuestionReport.objects.filter(question_id=question_id).delete()

            return ApiResponse.Success(message='Reports deleted successfully.')
        except Exception as e:
            return ApiResponse.InternalServerError(message=str(e))
