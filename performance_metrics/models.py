from django.db import models
from users.models import CustomUser
from questions.models import ExamType, Subject

class SubjectPerformance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subject_performances')
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, null=True, related_name='subject_performances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='performances')
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    unseen_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0)
    correct_percentage = models.FloatField(default=0)
    incorrect_percentage = models.FloatField(default=0)
    unanswered_percentage = models.FloatField(default=0)
    unseen_percentage = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'exam_type', 'subject')

    def __str__(self):
        return f"Performance for {self.user} - {self.exam_type} - {self.subject}"