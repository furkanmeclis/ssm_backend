from django.urls import path
from uni_rankings.views.uni_ranking_views import LocationList, UniversityListByLocation, MajorListByLocationAndUniversity, ProgramList

urlpatterns = [
    path('university/locations/', LocationList.as_view(), name='get_locations'),
    path('university/locations/<int:location_id>/universities/', UniversityListByLocation.as_view(), name='get_universities_by_location'),
    path('university/locations/<int:location_id>/universities/<int:university_id>/majors/', MajorListByLocationAndUniversity.as_view(), name='get_majors_by_location_and_university'),
    path('university/locations/<int:location_id>/universities/<int:university_id>/majors/<int:major_id>/programs/', ProgramList.as_view(), name='get_programs'),
]