from rest_framework import serializers
from topic_history.models import TopicHistory

class TopicHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicHistory
        fields = ['topic', 'history_data']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        history_data = representation.get('history_data', {})
        
        # Sort history_data by year in descending order
        sorted_history_data = dict(sorted(history_data.items(), key=lambda x: x[0], reverse=True))
        representation['history_data'] = sorted_history_data
        return representation
