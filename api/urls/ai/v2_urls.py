from django.urls import path
from ai.views.ai_views import SimpleChatView, SummarizeImageView, SolveImageView

urlpatterns = [
    path('chat/', SimpleChatView.as_view(), name='ai-simple-chat'),
    path('summarize-image/', SummarizeImageView.as_view(), name='ai-summarize-image'),
    path('solve-image/', SolveImageView.as_view(), name='ai-solve-image'),
]