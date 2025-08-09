from django.db import models

class ExamYear(models.Model):
    year = models.PositiveIntegerField(unique=True, verbose_name="Yıl")

    def __str__(self):
        return str(self.year)
    
    class Meta:
        verbose_name = "Sınav Yılı"
        verbose_name_plural = "Sınav Yılları"

class ExamType(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Ad")
    exam_years = models.ManyToManyField(ExamYear, related_name='exam_types', blank=True, verbose_name="Sınav Yılları")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Sınav Adı"
        verbose_name_plural = "Sınav Adları"

class Subject(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Ad")
    exam_types = models.ManyToManyField(ExamType, related_name='subjects', blank=True, verbose_name="Sınav Türleri")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"

class Topic(models.Model):
    name = models.CharField(max_length=255, verbose_name="Ad")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='topics', verbose_name="Ders")
    achievement_code = models.PositiveIntegerField(unique=True, verbose_name="Başarı Kodu")

    def __str__(self):
        return self.name + " - " + str(self.achievement_code)

    class Meta:
        verbose_name = "Konu"
        verbose_name_plural = "Konular"
        unique_together = ('name', 'subject')

class Question(models.Model):
    exam_year = models.ForeignKey(ExamYear, on_delete=models.SET_NULL, null=True, related_name='questions', verbose_name="Sınav Yılı")
    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True, related_name='questions', verbose_name="Sınav Türü")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='questions', verbose_name="Ders")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions', verbose_name="Konu")
    question_number = models.PositiveIntegerField(verbose_name="Soru Numarası")
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')], verbose_name="Doğru Cevap")
    difficulty_level = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 11)], null=True, blank=True, verbose_name="Zorluk Seviyesi")
    image_url = models.URLField(max_length=255, null=True, blank=True, verbose_name="Resim URL")
    video_solution_url = models.URLField(max_length=255, null=True, blank=True, verbose_name="Video Çözüm URL")

    def __str__(self):
        return f"S{self.question_number} - {self.exam_type.name if self.exam_type else 'N/A'} {self.exam_year.year if self.exam_year else 'N/A'}"

    class Meta:
        verbose_name = 'Soru'
        verbose_name_plural = 'Sorular'
        unique_together = ('exam_year', 'exam_type', 'subject', 'topic', 'question_number')
