from django.contrib import admin
from .models import Exam

class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_date', 'display_remaining_days', 'display_detailed_remaining_time')
    list_filter = ('exam_date',)
    search_fields = ('title',)
    ordering = ('exam_date',)
    readonly_fields = ('display_remaining_days', 'display_detailed_remaining_time')

    def display_remaining_days(self, obj):
        remaining_days, _ = obj.calculate_remaining_time()
        return f"{remaining_days} Gün" if remaining_days is not None else "Sınav tarihi geçti"
    display_remaining_days.short_description = "Kalan Gün"

    def display_detailed_remaining_time(self, obj):
        _, detailed_remaining_time = obj.calculate_remaining_time()
        return detailed_remaining_time or "Sınav tarihi geçti"
    display_detailed_remaining_time.short_description = "Detaylı Kalan Süre"

admin.site.register(Exam, ExamAdmin)
