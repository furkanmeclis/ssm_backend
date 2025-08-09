from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from utils.api_responses import ApiResponse
from rest_framework.views import APIView
from services.digitalocean_service import process_image_and_upload_to_digitalocean
from serializers.users_serializers import UserProfileSerializer
from django.db import transaction

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        """Handle GET requests for user profile."""
        user = request.user
        serializer = UserProfileSerializer(user)
        return ApiResponse.Success(data=serializer.data)

    def put(self, request):
        """Handle PUT requests for updating user profile."""
        user = request.user
        data = request.data.copy()
        profile_image = data.get('profile_image', None)
        serializer = UserProfileSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            # If there is a new profile image, process and upload it
            if profile_image:
                # Process and upload the image
                image_url = process_image_and_upload_to_digitalocean(profile_image, "profile_images", 600, 600)
                if image_url:
                    serializer.validated_data['profile_image'] = image_url

            serializer.save()
            return ApiResponse.Success(message='Profil başarıyla güncellendi.', data=serializer.data)
        
        return ApiResponse.BadRequest(message='Profil güncellenirken hata oluştu.')

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            user = request.user
            with transaction.atomic():
                user.delete()
            return ApiResponse.Success(message='Hesabınız ve tüm verileriniz başarıyla silindi.')
        except Exception as e:
            return ApiResponse.BadRequest(message='Hesabınız silinirken bir hata oluştu. Lütfen tekrar deneyin.')
