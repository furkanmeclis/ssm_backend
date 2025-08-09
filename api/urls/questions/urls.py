from django.urls import path
from questions.views.question_views import ExamYearList, TopicList, SubjectList, ExamTypeList

urlpatterns = [
    path('exam-years/', ExamYearList.as_view(), name='exam-year-list'),
    path('exam-types/', ExamTypeList.as_view(), name='exam-type-list'),
    path('subjects/', SubjectList.as_view(), name='subject-list'),
    path('topics/', TopicList.as_view(), name='topic-list'),
]