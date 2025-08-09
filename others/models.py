from django.db import models
from users.models import CustomUser

class BulkUploadStatus(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    )
    task_id = models.CharField(max_length=255, unique=True)
    task_type = models.CharField(max_length=255, blank=True, null=True) # E.g., 'questions', 'uni_rankings'
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True)  # Store error, warning, and success messages here.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_type} upload by {self.user.email if self.user else 'Unknown'}"
