from django.urls import path, include
from quizzes.views.quiz_views import CreateQuizzes, QuizGroupListView, QuizGroupDetailView, QuizDetailView
from quizzes.views.attempt_views import SubmitQuizAttempt, QuizAttemptListView, QuizAttemptDetailView, QuizGroupAttemptsView, QuizIDAttemptDetailView, SubmitDisplaySet
from quizzes.views.favorite_views import ToggleFavoriteQuestionView, FavoriteQuestionsListView, FavoriteSubjectsListView, FavoriteTopicsListView
from quizzes.views.question_display_views import QuestionDisplaySetViewSet, LatestFourQuizGroupsAndDisplaySetsView
from quizzes.views.incorrect_views import IncorrectQuestionsListView, IncorrectQuestionsSubjectsListView, IncorrectQuestionsTopicsListView, DeleteIncorrectQuestionView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'quizzes/display-sets', QuestionDisplaySetViewSet, basename='question-display-set')

urlpatterns = [
    path('quizzes/', CreateQuizzes.as_view(), name='create-quizzes'),
    path('quiz-groups/', QuizGroupListView.as_view(), name='quiz-group-list'),
    path('quiz-groups/<int:pk>/', QuizGroupDetailView.as_view(), name='quiz-group-detail'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:quiz_id>/submit/', SubmitQuizAttempt.as_view(), name='submit-quiz-attempt'),
    path('quizzes/display-sets/<int:display_set_id>/submit/', SubmitDisplaySet.as_view(), name='submit-display-set-attempt'),
    path('quizzes/attempts/', QuizAttemptListView.as_view(), name='quiz-attempt-list'),
    path('quizzes/attempts/<int:pk>/', QuizAttemptDetailView.as_view(), name='quiz-attempt-detail'),
    path('quizzes/<int:quiz_id>/attempts/', QuizIDAttemptDetailView.as_view(), name='quiz-id-attempt-detail'),
    path('quiz-groups/<int:quiz_group_id>/attempts/', QuizGroupAttemptsView.as_view(), name='quiz-group-attempts'),
    path('quizzes/incorrect-questions/', IncorrectQuestionsListView.as_view(), name='incorrect-questions-list'),
    path('quizzes/incorrect-questions/subjects/', IncorrectQuestionsSubjectsListView.as_view(), name='incorrect-questions-subjects-list'),
    path('quizzes/incorrect-questions/subjects/<int:subject_id>/topics/', IncorrectQuestionsTopicsListView.as_view(), name='incorrect-questions-topics-list'),
    path('quizzes/incorrect-questions/<int:pk>/', DeleteIncorrectQuestionView.as_view(), name='delete-incorrect-question'),
    path('quizzes/favorites/questions/toggle/', ToggleFavoriteQuestionView.as_view(), name='toggle-favorite-question'),
    path('quizzes/favorites/questions/', FavoriteQuestionsListView.as_view(), name='favorite-questions-list'),
    path('quizzes/favorites/subjects/', FavoriteSubjectsListView.as_view(), name='favorite-subjects-list'),
    path('quizzes/favorites/subjects/<int:subject_id>/topics/', FavoriteTopicsListView.as_view(), name='favorite-topics-list'),
    path('quizgroups-displaysets/', LatestFourQuizGroupsAndDisplaySetsView.as_view(), name='quizgroups-displaysets'),
    path('', include(router.urls)),
]
