from django.contrib import admin
from .models import MotivationalMessage, Quiz, MultiSubjectMotivationalMessage

class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0
    fields = ('id', 'questions_display', 'created_at')
    readonly_fields = ('id', 'questions_display', 'created_at')
    can_delete = False

    def questions_display(self, obj):
        return ", ".join(str(q) for q in obj.questions.all())
    questions_display.short_description = "Questions"

class QuizGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by')
    search_fields = ('name', 'created_by__username')
    inlines = [QuizInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'created_by')
        }),
        ('Exam Information', {
            'fields': ('exam_years', 'exam_types', 'subject', 'topic')
        }),
    )

class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'quiz_group', 'question_count', 'created_at')
    search_fields = ('quiz_group__name',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Number of Questions'

class QuestionDisplaySetAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by')
    search_fields = ('name', 'created_by__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('name', 'created_by')
        }),
        ('Exam Information', {
            'fields': ('exam_years', 'exam_types', 'subject', 'topic')
        }),
        ('Questions', {
            'fields': ('questions',)
        }),
    )

class IncorrectQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'quiz_attempt')
    search_fields = ('user__username', 'question__text')
    list_per_page = 20  # Reduce the number of records per page

class MotivationalMessageAdmin(admin.ModelAdmin):
    list_display = ('get_range_display', 'subject', 'message_preview', 'is_active')
    list_filter = ('success_rate_range', 'subject', 'is_active')
    search_fields = ('message',)
   
    def get_range_display(self, obj):
        return obj.get_success_rate_range_display()
    get_range_display.short_description = 'Başarı Oranı Aralığı'
   
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mesaj Önizleme'

admin.site.register(MotivationalMessage, MotivationalMessageAdmin)

class MultiSubjectMotivationalMessageAdmin(admin.ModelAdmin):
    list_display = ('get_range_display', 'message_preview', 'is_active')
    list_filter = ('success_rate_range', 'is_active')
    search_fields = ('message',)
   
    def get_range_display(self, obj):
        return obj.get_success_rate_range_display()
    get_range_display.short_description = 'Başarı Oranı Aralığı'
   
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mesaj Önizleme'

admin.site.register(MultiSubjectMotivationalMessage, MultiSubjectMotivationalMessageAdmin)
