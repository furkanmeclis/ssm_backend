from django.urls import path
from questions.views.question_views import QuestionDetailView

urlpatterns = [
    path('soru/<str:code>/', QuestionDetailView.as_view(), name='question_detail'),
]