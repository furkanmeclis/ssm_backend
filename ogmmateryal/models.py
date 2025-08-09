from django.db import models

class ExamSection(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(help_text="Order of the section in the exam")

    class Meta:
        verbose_name = "Sınav Türü"
        verbose_name_plural = "Sınav Türleri"

    def __str__(self):
        return self.name

class ExamSubject(models.Model):
    section = models.ForeignKey(ExamSection, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    question_count = models.IntegerField(help_text="Number of questions in this subject")

    class Meta:
        verbose_name = "Sınav Konusu"
        verbose_name_plural = "Sınav Konuları"

    def __str__(self):
        return f"{self.section.name} - {self.name}"

class ExamStructure(models.Model):
    name = models.CharField(max_length=100)
    sections = models.ManyToManyField(ExamSection, related_name='exam_structures')
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Sınav Yapısı"
        verbose_name_plural = "Sınav Yapıları"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.active:
            ExamStructure.objects.filter(active=True).update(active=False)
        super().save(*args, **kwargs)
