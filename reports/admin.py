from django.contrib import admin
from .models import ReportType, QuestionReport
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import path
from django.shortcuts import redirect, get_object_or_404

@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_filter = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name',),
        }),
    )

@admin.register(QuestionReport)
class QuestionReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'report_type', 'created_at')
    search_fields = ('user__email', 'question__question_number', 'report_type__name')
    list_filter = ('report_type', 'created_at')
    readonly_fields = ('user', 'question', 'report_type', 'report_detail', 'created_at')

    fieldsets = (
        (None, {
            'fields': ('user', 'question', 'report_type', 'report_detail', 'created_at'),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/delete_reports_of_same_type/', self.admin_site.admin_view(self.delete_reports_of_same_type_view), name='delete_reports_of_same_type'),
            path('<int:object_id>/delete_all_reports_for_question/', self.admin_site.admin_view(self.delete_all_reports_for_question_view), name='delete_all_reports_for_question'),
        ]
        return custom_urls + urls

    def delete_reports_of_same_type_view(self, request, object_id):
        report = get_object_or_404(QuestionReport, id=object_id)
        QuestionReport.objects.filter(
            question=report.question, 
            report_type=report.report_type
        ).delete()
        messages.success(request, "Seçilen raporlar ve aynı türdeki tüm raporlar silindi.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    def delete_all_reports_for_question_view(self, request, object_id):
        report = get_object_or_404(QuestionReport, id=object_id)
        QuestionReport.objects.filter(question=report.question).delete()
        messages.success(request, "Seçilen raporlar ve aynı soruya ait tüm raporlar silindi.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_buttons'] = {
            'delete_reports_of_same_type_url': f'{object_id}/delete_reports_of_same_type/',
            'delete_all_reports_for_question_url': f'{object_id}/delete_all_reports_for_question/',
        }
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    actions = ['delete_reports_of_same_type_action', 'delete_all_reports_for_question_action']

    def delete_reports_of_same_type_action(self, request, queryset):
        for report in queryset:
            QuestionReport.objects.filter(
                question=report.question, 
                report_type=report.report_type
            ).delete()
        messages.success(request, "Seçilen raporlar ve aynı türdeki tüm raporlar silindi.")

    delete_reports_of_same_type_action.short_description = 'Seçilen raporlar için aynı türdeki tüm raporları sil'

    def delete_all_reports_for_question_action(self, request, queryset):
        for report in queryset:
            QuestionReport.objects.filter(question=report.question).delete()
        messages.success(request, "Seçilen raporlar ve aynı soruya ait tüm raporlar silindi.")

    delete_all_reports_for_question_action.short_description = 'Seçilen soru için tüm raporları sil'
