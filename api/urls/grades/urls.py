from django.urls import path
from grades.views.grade_views import GradeListView, UserGradeView

urlpatterns = [
    path('grades/', GradeListView.as_view(), name='grade-list'),
    path('user/grade/', UserGradeView.as_view(), name='user-grade'),
]
