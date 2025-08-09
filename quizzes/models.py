from django.db import models
from questions.models import Question, ExamYear, ExamType, Subject, Topic
from users.models import CustomUser
from django.db.models import JSONField

class QuizGroupTopic(models.Model):
  quiz_group = models.ForeignKey('QuizGroup', on_delete=models.CASCADE)
  topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

  class Meta:
    db_table = 'quizzes_quizgroup_topic'

class QuestionDisplaySetTopic(models.Model):
  question_display_set = models.ForeignKey('QuestionDisplaySet', on_delete=models.CASCADE)
  topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

  class Meta:
    db_table = 'quizzes_questiondisplayset_topic'

class QuizGroup(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    exam_years = models.ManyToManyField(ExamYear, related_name='quiz_groups')
    exam_types = models.ManyToManyField(ExamType, related_name='quiz_groups')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='quiz_groups')
    topic = models.ManyToManyField(Topic, through='QuizGroupTopic', related_name='quiz_groups_m2m')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class QuestionDisplaySet(models.Model):
    name = models.CharField(max_length=255)
    questions = models.ManyToManyField(Question, related_name='display_sets')
    exam_years = models.ManyToManyField(ExamYear, related_name='display_sets')
    exam_types = models.ManyToManyField(ExamType, related_name='display_sets')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='display_sets')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='display_sets')
    created_at = models.DateTimeField(auto_now_add=True)
    topic = models.ManyToManyField(Topic, through='QuestionDisplaySetTopic', related_name='display_sets_m2m')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}"

class Quiz(models.Model):
    quiz_group = models.ForeignKey(QuizGroup, on_delete=models.CASCADE, related_name='quizzes')
    questions = models.ManyToManyField(Question, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quiz_group.name} - Quiz {self.pk}"
    

class QuizAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    unanswered_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=0)
    motivational_message = models.TextField(null=True, blank=True)
    details = JSONField(default=dict)  # Store question details as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attempt by {self.user} on {self.quiz}"

class IncorrectQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='incorrect_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='incorrect_attempts')
    user_answer = models.CharField(max_length=255, null=True, blank=True)
    correct_answer = models.CharField(max_length=255)
    user_time = models.FloatField(null=True, blank=True)
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='incorrect_questions')
    question_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['-quiz_attempt__created_at']

    def __str__(self):
        return f"Incorrect attempt by {self.user} for {self.question} in attempt {self.quiz_attempt.id}"

class DisplaySetAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='display_set_attempts')
    display_set = models.ForeignKey(QuestionDisplaySet, on_delete=models.CASCADE, related_name='attempts')
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

class DisplaySetIncorrectQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='display_set_incorrect_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='display_set_incorrect_attempts')
    user_answer = models.CharField(max_length=255, null=True, blank=True)
    correct_answer = models.CharField(max_length=255)
    user_time = models.FloatField(null=True, blank=True)
    display_set_attempt = models.ForeignKey(DisplaySetAttempt, on_delete=models.CASCADE, related_name='incorrect_questions')
    question_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['-display_set_attempt__created_at']

    def __str__(self):
        return f"Incorrect attempt by {self.user} for {self.question} in attempt {self.display_set_attempt.id}"
    
class FavoriteQuestion(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorite_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='favorited_by')
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, related_name='favorite_questions')
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.SET_NULL, null=True, related_name='favorite_questions')
    question_order = models.PositiveIntegerField() 
    created_at = models.DateTimeField(auto_now_add=True)

    # Ensure that a user can only favorite the same question once
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'question')

    def __str__(self):
        return f"Favorite by {self.user.email} - Question ID {self.question.id}"

class MotivationalMessage(models.Model):
    SUCCESS_RATE_RANGES = [
        (1, '%0-20'),
        (2, '%20-40'),
        (3, '%40-60'),
        (4, '%60-80'),
        (5, '%80-100'),
    ]
   
    subject = models.ForeignKey(Subject, verbose_name="Ders", on_delete=models.CASCADE, null=True, blank=True,
                               related_name='motivational_messages')
    success_rate_range = models.IntegerField(verbose_name="Başarı Oranı Aralığı", choices=SUCCESS_RATE_RANGES)
    message = models.TextField(verbose_name="Mesaj")
    is_active = models.BooleanField(verbose_name="Aktif", default=True)
   
    class Meta:
        ordering = ['success_rate_range', 'subject']
        verbose_name = "Motivasyon Mesajı"
        verbose_name_plural = "Motivasyon Mesajları"
   
    def __str__(self):
        subject_name = self.subject.name if self.subject else "Genel"
        return f"{subject_name} - {self.get_success_rate_range_display()}"

class MultiSubjectMotivationalMessage(models.Model):
    SUCCESS_RATE_RANGES = [
        (1, '%0-20'),
        (2, '%20-40'),
        (3, '%40-60'),
        (4, '%60-80'),
        (5, '%80-100'),
    ]
   
    success_rate_range = models.IntegerField(verbose_name="Başarı Oranı Aralığı", choices=SUCCESS_RATE_RANGES)
    message = models.TextField(verbose_name="Mesaj")
    is_active = models.BooleanField(verbose_name="Aktif", default=True)
   
    class Meta:
        ordering = ['success_rate_range']
        verbose_name = "Çoklu Ders Motivasyon Mesajı"
        verbose_name_plural = "Çoklu Ders Motivasyon Mesajları"
   
    def __str__(self):
        return f"Çoklu Ders - {self.get_success_rate_range_display()}"
