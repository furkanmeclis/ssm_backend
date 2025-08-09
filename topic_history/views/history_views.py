from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.api_responses import ApiResponse
from serializers.topic_history_serializers import TopicHistorySerializer

from topic_history.models import TopicHistory

class QuizAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TopicHistorySerializer

    def get(self, request, topic_id):
        try:
            topic_history = TopicHistory.objects.get(topic=topic_id, history_data__isnull=False)
        except TopicHistory.DoesNotExist:
            return ApiResponse.NotFound("Konu geçmişi bulunamadı.")
        
        serializer = self.serializer_class(topic_history)
        return ApiResponse.Success(data=serializer.data)
