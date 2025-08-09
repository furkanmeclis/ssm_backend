from django.urls import path
from exams.views.exam_views import ExamAPIView, ExamSelectionAPIView

urlpatterns = [
    path('exams/', ExamAPIView.as_view(), name='exams'),
    path('exams/select/', ExamSelectionAPIView.as_view(), name='exam-selection'),
]
