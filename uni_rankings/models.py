from django.db import models

class University(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Üniversite Adı")

    class Meta:
        verbose_name = "Üniversite"
        verbose_name_plural = "Üniversiteler"

    def __str__(self):
        return self.name

class Major(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Bölüm Adı")

    class Meta:
        verbose_name = "Bölüm"
        verbose_name_plural = "Bölümler"

    def __str__(self):
        return self.name

class ExamYear(models.Model):
    year = models.PositiveIntegerField(unique=True, verbose_name="Yıl")

    class Meta:
        verbose_name = "Sınav Yılı"
        verbose_name_plural = "Sınav Yılları"

    def __str__(self):
        return str(self.year)

class Location(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Konum Adı")

    class Meta:
        verbose_name = "Konum"
        verbose_name_plural = "Konumlar"

    def __str__(self):
        return self.name

class Program(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='programs', verbose_name="Bölüm")
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='programs', verbose_name="Üniversite")
    exam_year = models.ForeignKey(ExamYear, on_delete=models.CASCADE, related_name='programs', verbose_name="Sınav Yılı")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='programs', null=True, blank=True, verbose_name="Konum")
    ranking = models.PositiveIntegerField(null=True, blank=True, verbose_name="Sıralama")
    min_score = models.FloatField(null=True, blank=True, verbose_name="Minimum Puan")
    max_score = models.FloatField(null=True, blank=True, verbose_name="Maksimum Puan")
    program_code = models.PositiveIntegerField(null=True, blank=True, verbose_name="Program Kodu")
    program_type = models.CharField(max_length=255, null=True, blank=True, verbose_name="Program Türü")
    education_length = models.PositiveIntegerField(null=True, blank=True, verbose_name="Eğitim Süresi")

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programlar"

    def __str__(self):
        return f"{self.major} at {self.university.name}"
