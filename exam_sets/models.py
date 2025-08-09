from django.conf import settings
from django.db import models
from questions.models import ExamYear, ExamType, Subject, Topic, Question
from users.models import CustomUser
from django.db.models import JSONField

class ExamSet(models.Model):
    name = models.CharField(max_length=255, verbose_name="İsim")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    exam_years = models.ManyToManyField(ExamYear, related_name='exam_sets', verbose_name="Sınav Yılları")
    exam_types = models.ManyToManyField(ExamType, related_name='exam_sets', verbose_name="Sınav Türleri")
    topics = models.ManyToManyField(Topic, related_name='exam_sets', blank=True, verbose_name="Konular")
    ordered_subjects = models.ManyToManyField(
        Subject, 
        through='ExamSetSubject',
        related_name='ordered_exam_sets', 
        verbose_name="Sıralı Dersler"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif Mi")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sınav Seti"
        verbose_name_plural = "Sınav Setleri"
        unique_together = ('name', 'created_at')

class ExamSetSubject(models.Model):
    exam_set = models.ForeignKey('ExamSet', on_delete=models.CASCADE, verbose_name="Sınav Seti")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Ders")
    order = models.PositiveIntegerField(default=0, verbose_name="Sıralama")

    class Meta:
        ordering = ['order']
        unique_together = ('exam_set', 'subject')
        verbose_name = "Sınav Seti Ders Sıralaması"
        verbose_name_plural = "Sınav Seti Ders Sıralamaları"

    def __str__(self):
        return f"{self.subject.name} - Sıra: {self.order}"

class UserExamConfiguration(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='exam_configurations'
    )
    exam_years = models.ManyToManyField(ExamYear, blank=True, related_name='+')
    exam_types = models.ManyToManyField(ExamType, blank=True, related_name='+')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='+')
    topics = models.ManyToManyField(Topic, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (User: {self.created_by.username})"

    class Meta:
        ordering = ['-created_at']

class ExamSetQuizGroup(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_quiz_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    exam_set = models.ForeignKey('exam_sets.ExamSet', on_delete=models.CASCADE, related_name='quiz_groups')
    exam_years = models.ManyToManyField(ExamYear, related_name='exam_set_quiz_groups')
    exam_types = models.ManyToManyField(ExamType, related_name='exam_set_quiz_groups')
    subjects = models.ManyToManyField(Subject, related_name='exam_set_quiz_groups')
    topic = models.ManyToManyField(Topic, related_name='exam_set_quiz_groups')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class ExamSetQuiz(models.Model):
    quiz_group = models.ForeignKey(ExamSetQuizGroup, on_delete=models.CASCADE, related_name='quizzes')
    questions = models.ManyToManyField(Question, related_name='exam_set_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quiz_group.name} - Quiz {self.pk}"

class ExamSetDisplaySet(models.Model):
    name = models.CharField(max_length=255)
    questions = models.ManyToManyField(Question, related_name='exam_set_display_sets')
    exam_set = models.ForeignKey('exam_sets.ExamSet', on_delete=models.CASCADE, related_name='display_sets')
    exam_years = models.ManyToManyField(ExamYear, related_name='exam_set_display_sets')
    exam_types = models.ManyToManyField(ExamType, related_name='exam_set_display_sets')
    subjects = models.ManyToManyField(Subject, related_name='exam_set_display_sets')
    topic = models.ManyToManyField(Topic, related_name='exam_set_display_sets')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_display_sets')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}"

class ExamSetQuizAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_quiz_attempts')
    quiz = models.ForeignKey(ExamSetQuiz, on_delete=models.CASCADE, related_name='attempts')
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0)
    motivational_message = models.TextField(null=True, blank=True)
    details = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attempt by {self.user} on {self.quiz}"

class ExamSetIncorrectQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_incorrect_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='exam_set_incorrect_attempts')
    user_answer = models.CharField(max_length=255, null=True, blank=True)
    correct_answer = models.CharField(max_length=255)
    user_time = models.FloatField(null=True, blank=True)
    quiz_attempt = models.ForeignKey(ExamSetQuizAttempt, on_delete=models.CASCADE, related_name='incorrect_questions')
    question_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['-quiz_attempt__created_at']

    def __str__(self):
        return f"Incorrect attempt by {self.user} for {self.question} in exam set attempt {self.quiz_attempt.id}"

class ExamSetDisplaySetAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_display_set_attempts')
    display_set = models.ForeignKey(ExamSetDisplaySet, on_delete=models.CASCADE, related_name='attempts')
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0)
    motivational_message = models.TextField(null=True, blank=True)
    details = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attempt by {self.user} on {self.display_set}"

class ExamSetDisplaySetIncorrectQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exam_set_display_set_incorrect_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='exam_set_display_set_incorrect_attempts')
    user_answer = models.CharField(max_length=255, null=True, blank=True)
    correct_answer = models.CharField(max_length=255)
    user_time = models.FloatField(null=True, blank=True)
    display_set_attempt = models.ForeignKey(ExamSetDisplaySetAttempt, on_delete=models.CASCADE, related_name='incorrect_questions')
    question_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['-display_set_attempt__created_at']

    def __str__(self):
        return f"Incorrect attempt by {self.user} for {self.question} in display set attempt {self.display_set_attempt.id}"
