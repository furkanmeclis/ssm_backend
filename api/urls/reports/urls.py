from django.urls import path
from reports.views.report_views import QuestionReportCreateView, ReportTypeListView

urlpatterns = [
    path('report/types/', ReportTypeListView.as_view(), name='report-type-list'),
    path('questions/<int:question_id>/report/', QuestionReportCreateView.as_view(), name='question-report-create'),
]