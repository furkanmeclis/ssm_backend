from django.contrib import admin
from .models import ExamSet, ExamSetSubject

class ExamSetSubjectInline(admin.TabularInline):
    model = ExamSetSubject
    extra = 1
    verbose_name = "Ders Sıralaması"
    verbose_name_plural = "Ders Sıralamaları"

class ExamSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_active')
    filter_horizontal = ('exam_years', 'exam_types', 'topics')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'exam_years', 'exam_types')
    inlines = [ExamSetSubjectInline]

admin.site.register(ExamSet, ExamSetAdmin)
