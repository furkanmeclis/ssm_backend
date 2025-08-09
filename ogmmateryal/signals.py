from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import ExamStructure

@receiver(post_save, sender=ExamStructure)
def clear_exam_structure_cache(sender, instance, **kwargs):
    if instance.active:
        cache.delete('active_exam_structure')
