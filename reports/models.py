from django.db import models
from users.models import CustomUser
from questions.models import Question

class ReportType(models.Model):
    name = models.CharField(max_length=255, verbose_name='Adı')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Rapor Türü'
        verbose_name_plural = 'Rapor Türleri'

class QuestionReport(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reports', verbose_name='Soru')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports', verbose_name='Kullanıcı')
    report_type = models.ForeignKey(ReportType, on_delete=models.CASCADE, related_name='question_reports', verbose_name='Rapor Türü')
    report_detail = models.TextField(blank=True, null=True, verbose_name='Rapor Detayı')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')

    class Meta:
        unique_together = ('user', 'question', 'report_type')
        ordering = ['-created_at']

        verbose_name = 'Soru Raporu'
        verbose_name_plural = 'Soru Raporları'

    def __str__(self):
        return f"{self.user} raporladı: {self.question}"
