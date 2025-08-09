from django.urls import path, include
from quizzes.views.v2.quiz_views import CreateQuizzes
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from quizzes.views.v2.question_display_views import QuestionDisplaySetViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'quizzes/display-sets', QuestionDisplaySetViewSet, basename='question-display-set')

urlpatterns = [
    path('quizzes/', CreateQuizzes.as_view(), name='create-quizzes'),
    path('', include(router.urls)),
]
