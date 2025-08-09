from rest_framework.views import APIView
from utils.api_responses import ApiResponse
from uni_rankings.models import Location, Major, Program, University
from django.db.models import F

class LocationList(APIView):
    def get(self, request, *args, **kwargs):
        locations = Location.objects.all().order_by('name').values('id', 'name')
        if not locations.exists():
            return ApiResponse.NotFound(message="Hiçbir konum bulunamadı.")
        
        return ApiResponse.Success(data=list(locations))

class UniversityListByLocation(APIView):
    def get(self, request, location_id, *args, **kwargs):
        universities = University.objects.filter(
            programs__location_id=location_id
        ).distinct().values('id', 'name').order_by('name')
        
        if not universities.exists():
            return ApiResponse.NotFound(message="Bu konum için hiçbir üniversite bulunamadı.")
        
        return ApiResponse.Success(data=list(universities))

class MajorListByLocationAndUniversity(APIView):
    def get(self, request, location_id, university_id, *args, **kwargs):
        majors = Major.objects.filter(
            programs__location_id=location_id,
            programs__university_id=university_id
        ).distinct().values('id', 'name').order_by('name')
        
        if not majors.exists():
            return ApiResponse.NotFound(message="Bu konum ve üniversite için hiçbir bölüm bulunamadı.")
        
        return ApiResponse.Success(data=list(majors))

class ProgramList(APIView):
    def get(self, request, location_id, university_id, major_id, *args, **kwargs):
        programs = Program.objects.filter(
            location_id=location_id,
            university_id=university_id,
            major_id=major_id
        ).annotate(
            year=F('exam_year__year')
        ).values(
            'year', 'program_code', 'ranking', 'min_score', 'max_score', 'program_type', 'education_length'
        )
        
        if not programs.exists():
            return ApiResponse.NotFound(message="Verilen filtreler için hiçbir program bulunamadı.")
        
        return ApiResponse.Success(data=list(programs))
