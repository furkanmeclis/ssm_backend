from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Exam(models.Model):
    title = models.CharField(max_length=255)
    exam_date = models.DateTimeField()
    is_major_exam = models.BooleanField(default=False)
    display_in_homepage = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def calculate_remaining_time(self):
        if self.exam_date:
            remaining_time = self.exam_date - timezone.localtime()
            if remaining_time.total_seconds() > 0:
                remaining_days = remaining_time.days
                hours, remainder = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                detailed_remaining_time = f"{remaining_days} Gün, {hours} Saat, {minutes} Dakika, {seconds} Saniye"
                return remaining_days, detailed_remaining_time
        return None, None

    class Meta:
        verbose_name = 'Sınav'
        verbose_name_plural = 'Sınavlar'
