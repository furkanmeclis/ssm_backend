from django.urls import path
from others.views.other_views import check_task_status, upload_history, upload_history_details, base_view, question_redirect_view

urlpatterns = [
    path('check-task-status/<str:task_type>/', check_task_status, name='check_task_status'),
    path('upload-history/<str:task_type>/', upload_history, name='upload_history'),
    path('upload-history/details/<int:upload_id>/', upload_history_details, name='upload_history_details'),
    path('soru/<str:question_code>/', question_redirect_view, name='question_redirect'),
    path('', base_view, name='base_view'),
]
