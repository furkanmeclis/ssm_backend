from django.urls import path
from topic_history.views.history_views import QuizAttemptDetailView

urlpatterns = [
    path('topic/<int:topic_id>/history/', QuizAttemptDetailView.as_view(), name='topic_history'),
]
