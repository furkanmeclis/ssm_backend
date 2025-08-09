from django.urls import path, include
from rest_framework.routers import DefaultRouter
from exam_sets.views.exam_sets_views import *
from exam_sets.views.exam_set_attempt_views import *

router = DefaultRouter()
router.register(r'exam-sets', ExamSetViewSet, basename='exam-set')
router.register(r'user-exam-configurations', UserExamConfigurationViewSet, basename='user-exam-configuration')

urlpatterns = [
    path('', include(router.urls)),
    path('exam-set-quizzes/<int:quiz_id>/submit/', SubmitExamSetQuizAttempt.as_view(), name='submit-exam-set-quiz'),
    path('exam-set-quizzes/attempts/', ExamSetQuizAttemptListView.as_view(), name='exam-set-quiz-attempt-list'),
    path('exam-set-quizzes/<int:pk>/', ExamSetQuizAttemptDetailView.as_view(), name='exam-set-quiz-attempt-detail'),
    path('exam-set-quizzes/<int:quiz_id>/attempts/', ExamSetQuizIDAttemptDetailView.as_view(), name='exam-set-quiz-id-attempts'),
    path('exam-set-quiz-groups/<int:quiz_group_id>/attempts/', ExamSetQuizGroupAttemptsView.as_view(), name='exam-set-quiz-group-attempts'),

    path('exam-set-display-sets/<int:display_set_id>/submit/', SubmitExamSetDisplaySet.as_view(), name='submit-exam-set-display-set'),
    path('exam-set-display-sets/attempts/', ExamSetDisplaySetAttemptListView.as_view(), name='exam-set-display-set-attempt-list'),
    path('exam-set-display-sets/attempts/<int:pk>/', ExamSetDisplaySetAttemptDetailView.as_view(), name='exam-set-display-set-attempt-detail'),
    path('exam-set-display-sets/<int:display_set_id>/attempts/', ExamSetDisplaySetIDAttemptDetailView.as_view(), name='exam-set-display-set-id-attempts'),
]