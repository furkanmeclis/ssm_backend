from django.contrib import admin
from .models import ExamSection, ExamSubject, ExamStructure

class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1

class ExamSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    inlines = [ExamSubjectInline]

class ExamStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    filter_horizontal = ['sections']
    actions = ['make_active']

    def make_active(self, request, queryset):
        queryset.update(active=True)
    make_active.short_description = "Mark selected structures as active"

admin.site.register(ExamSection, ExamSectionAdmin)
admin.site.register(ExamStructure, ExamStructureAdmin)
