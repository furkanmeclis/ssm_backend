from django.db import models
from questions.models import Topic

class TopicHistory(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic_histories')
    history_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Konu Geçmişi"
        verbose_name_plural = "Konu Geçmişleri"

    def __str__(self):
        return f"{self.id} - {self.topic.name}(#{self.topic.pk})"
