from django.urls import path
from performance_metrics.views.performance_views import ExamTypePerformanceView, SubjectPerformanceDetailView, SubjectTopicsPerformanceView

urlpatterns = [
    path('exam-types/performance/', ExamTypePerformanceView.as_view(), name='exam-type-performance'),
    path('exam-types/subjects/<int:subject_id>/performance/', SubjectPerformanceDetailView.as_view(), name='subject-performance'),
    path('exam-types/subjects/<int:subject_id>/topics/', SubjectTopicsPerformanceView.as_view(), name='subject-topics-performance'),
]
