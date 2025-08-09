from django.core.management.base import BaseCommand
from questions.models import Topic, Subject, ExamType
import time

class Command(BaseCommand):
    help = 'Compare filtering methods with real data'

    def handle(self, *args, **kwargs):
        year_ids = [1]  # Example year IDs
        type_ids = [1]  # Example exam type IDs
        subject_id = 360  # Example subject ID

        # Old method: Filtering without considering questions
        start_time = time.time()
        exam_types = ExamType.objects.filter(
            exam_years__id__in=year_ids
        ).distinct()

        for year_id in year_ids:
            exam_types = exam_types.filter(exam_years__id=year_id)
        old_method_time = time.time() - start_time
        print(f"Old method time: {old_method_time:.6f} seconds")

        # New method: Filtering with questions
        start_time = time.time()
        exam_types_with_questions = ExamType.objects.filter(
            exam_years__id__in=year_ids,
            subjects__topics__questions__isnull=False
        ).distinct()

        for year_id in year_ids:
            exam_types_with_questions = exam_types_with_questions.filter(
                exam_years__id=year_id,
                subjects__topics__questions__isnull=False
            )
        new_method_time = time.time() - start_time
        print(f"New method time: {new_method_time:.6f} seconds")

        # Similarly for Subjects
        start_time = time.time()
        subjects = Subject.objects.filter(
            exam_types__id__in=type_ids,
            exam_types__exam_years__id__in=year_ids
        ).distinct()

        for type_id in type_ids:
            subjects = subjects.filter(exam_types__id=type_id)
        old_subject_time = time.time() - start_time
        print(f"Old subject filtering time: {old_subject_time:.6f} seconds")

        start_time = time.time()
        subjects_with_questions = Subject.objects.filter(
            exam_types__id__in=type_ids,
            exam_types__exam_years__id__in=year_ids,
            topics__questions__isnull=False
        ).distinct()

        for type_id in type_ids:
            subjects_with_questions = subjects_with_questions.filter(
                exam_types__id=type_id,
                topics__questions__isnull=False
            )
        new_subject_time = time.time() - start_time
        print(f"New subject filtering time: {new_subject_time:.6f} seconds")

        # Similarly for Topics
        start_time = time.time()
        topics = Topic.objects.filter(
            subject__id=subject_id,
            subject__exam_types__id__in=type_ids,
            subject__exam_types__exam_years__id__in=year_ids
        ).distinct()
        old_topic_time = time.time() - start_time
        print(f"Old topic filtering time: {old_topic_time:.6f} seconds")

        start_time = time.time()
        topics_with_questions = Topic.objects.filter(
            subject__id=subject_id,
            subject__exam_types__id__in=type_ids,
            subject__exam_types__exam_years__id__in=year_ids,
            questions__isnull=False
        ).distinct()
        new_topic_time = time.time() - start_time
        print(f"New topic filtering time: {new_topic_time:.6f} seconds")
