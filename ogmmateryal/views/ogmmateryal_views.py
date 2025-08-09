import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.api_responses import ApiResponse
from ogmmateryal.models import ExamStructure
from serializers.exam_serializers import ExamStructureSerializer
from django.core.cache import cache

class YKSPuanHesaplamaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = "active_exam_structure"
        cached_structure = cache.get(cache_key)
        
        if cached_structure:
            return ApiResponse.Success(data=cached_structure)
        
        try:
            current_structure = ExamStructure.objects.get(active=True)
            serializer = ExamStructureSerializer(current_structure)
            serialized_data = serializer.data
            
            # Cache the structure data
            cache.set(cache_key, serialized_data, timeout=None)  # Cache indefinitely
            return ApiResponse.Success(data=serialized_data)
        except ExamStructure.DoesNotExist:
            return ApiResponse.NotFound("Aktif sınav yapısı bulunamadı.")

    def post(self, request):
        data = request.data

        # Fetch the active exam structure from cache or DB
        cache_key = "active_exam_structure"
        current_structure = cache.get(cache_key)

        if not current_structure:
            try:
                current_structure = ExamStructure.objects.get(active=True)
                # Cache the structure data
                serializer = ExamStructureSerializer(current_structure)
                current_structure = serializer.data
                cache.set(cache_key, current_structure, timeout=None)  # Cache indefinitely
            except ExamStructure.DoesNotExist:
                return ApiResponse.NotFound("Aktif sınav yapısı bulunamadı.")

        if not self.validate_input(data, current_structure):
            return ApiResponse.BadRequest("Geçersiz veri biçimi. Lütfen doğru yapıyı kullanın.")

        # Convert structured data to the required flat list format
        flattened_data = self.flatten_data(data, current_structure)

        try:
            response = requests.post(
                'https://ogmmateryal.eba.gov.tr/yks-puan-hesaplama',
                json=flattened_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                processed_data = self.process_response(response.json())
                return ApiResponse.Success(data=processed_data)
            else:
                return ApiResponse.InternalServerError("YKS puan hesaplama servisi yanıt vermedi.")
        except Exception as e:
            return ApiResponse.InternalServerError("YKS puan hesaplama servisi yanıt vermedi.")

    def validate_input(self, data, structure):
        try:
            for section in structure['sections']:
                if section['name'] not in data:
                    return False
                for subject in section['subjects']:
                    if subject['name'] not in data[section['name']]:
                        return False
            return True
        except KeyError:
            return False

    def flatten_data(self, data, structure):
        flat_list = []
        for section in structure['sections']:
            for subject in section['subjects']:
                flat_list.append(data[section['name']][subject['name']])
        return flat_list

    def process_response(self, response_data):
        # Process the response from the external API and structure it as required

        structured_data = {
            'tyt': {
                'puan': {
                    'ham': response_data[0]['tytPuani'],
                    'yerlestirme': response_data[3]['tytPuani']
                },
                'siralama': {
                    'ham': response_data[0]['tytAralik'],
                    'yerlestirme': response_data[3]['tytAralik']
                }
            },
            'ayt': {
                'puan': {
                    'sayisal': {
                        'ham': response_data[1]['sayisalPuani'],
                        'yerlestirme': response_data[4]['sayisalPuani']
                    },
                    'esit_agirlik': {
                        'ham': response_data[1]['esitAgirlikPuani'],
                        'yerlestirme': response_data[4]['esitAgirlikPuani']
                    },
                    'sozel': {
                        'ham': response_data[1]['sozelPuani'],
                        'yerlestirme': response_data[4]['sozelPuani']
                    }
                },
                'siralama': {
                    'sayisal': {
                        'ham': response_data[1]['sayAralik'],
                        'yerlestirme': response_data[4]['sayAralik']
                    },
                    'esit_agirlik': {
                        'ham': response_data[1]['eaAralik'],
                        'yerlestirme': response_data[4]['eaAralik']
                    },
                    'sozel': {
                        'ham': response_data[1]['sozAralik'],
                        'yerlestirme': response_data[4]['sozAralik']
                    }
                }
            },
            'dil': {
                'puan': {
                    'ham': response_data[2]['dilPuani'],
                    'yerlestirme': response_data[5]['dilPuani']
                },
                'siralama': {
                    'ham': response_data[2]['dilAralik'],
                    'yerlestirme': response_data[5]['dilAralik']
                }
            }
        }

        return structured_data
