from django.contrib import admin
from django import forms
import pandas as pd
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import admin, messages
from .models import ExamYear, ExamType, Subject, Topic, Question
from django.utils.translation import gettext_lazy as _
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from .tasks import process_bulk_upload_questions
from django.urls import reverse
from others.views.other_views import upload_history
from django.utils.safestring import mark_safe
import os
import boto3
import uuid

class ExamTypeInline(admin.TabularInline):
    model = ExamType.exam_years.through
    extra = 1
    verbose_name = "Bağlı Sınav Türü"
    verbose_name_plural = "Bağlı Sınav Türleri"

class SubjectInline(admin.TabularInline):
    model = Subject.exam_types.through
    extra = 1
    verbose_name = "Bağlı Ders"
    verbose_name_plural = "Bağlı Dersler"

@admin.register(ExamYear)
class ExamYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'exam_types_count')
    search_fields = ('year',)
    inlines = [ExamTypeInline]

    def exam_types_count(self, obj):
        return obj.exam_types.count()
    exam_types_count.short_description = 'Sınav Türü Sayısı'

    def has_delete_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return ['year']

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_years_count', 'subjects_count')
    search_fields = ('name',)
    inlines = [SubjectInline]
    exclude = ('exam_years',)
    list_filter = ('exam_years',)

    def exam_years_count(self, obj):
        return obj.exam_years.count()
    exam_years_count.short_description = 'Sınav Yılı Sayısı'

    def subjects_count(self, obj):
        return obj.subjects.count()
    subjects_count.short_description = 'Ders Sayısı'

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_types_count', 'topics_count')
    search_fields = ('name',)
    list_filter = ('exam_types',)

    def exam_types_count(self, obj):
        return obj.exam_types.count()
    exam_types_count.short_description = 'Sınav Türü Sayısı'

    def topics_count(self, obj):
        return obj.topics.count()
    topics_count.short_description = 'Konu Sayısı'

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'achievement_code')
    search_fields = ('name', 'subject__name', 'achievement_code')
    list_filter = ('subject',)

    def subjects_count(self, obj):
        return obj.subjects.count()
    subjects_count.short_description = 'Ders Sayısı'

    def has_delete_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return ['achievement_code']

class MultipleChoiceFilter(admin.SimpleListFilter):
    title = _('exam year')
    parameter_name = 'exam_year'

    def lookups(self, request, model_admin):
        years = set([year.year for year in ExamYear.objects.all()])
        return [(year, year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(exam_year__year__in=self.value().split(','))
        return queryset

class QuestionUploadForm(forms.Form):
    excel_file = forms.FileField()

class ColumnMappingForm(forms.Form):
    exam_type = forms.ChoiceField(label="Sınav Adı Sütunu (Örneğin: 'TYT')")
    exam_year = forms.ChoiceField(label="Sınav Yılı Sütunu (Örneğin: '2024')")
    question_number = forms.ChoiceField(label="Soru Numarası Sütunu (Örneğin: '1')")
    subject = forms.ChoiceField(label="Ders Adı Sütunu (Örneğin: 'Türkçe')")
    correct_answer = forms.ChoiceField(label="Cevap Anahtarı Sütunu (Örneğin: 'A')")
    
    # Optional fields with a skip checkbox
    achievement_code = forms.ChoiceField(label="Kazanım Kodu Sütunu (Örneğin: '1623')", required=False)
    skip_achievement_code = forms.BooleanField(label="Kazanım Kodunu Atla", required=False)
    
    difficulty_level = forms.ChoiceField(label="Zorluk Seviyesi Sütunu (Örneğin: '5')", required=False)
    skip_difficulty_level = forms.BooleanField(label="Zorluk Seviyesini Atla", required=False)
    
    video_solution_url = forms.ChoiceField(label="Video Çözüm URL Sütunu (Örneğin: 'https://example.com/video.mp4')", required=False)
    skip_video_solution_url = forms.BooleanField(label="Video Çözüm URL'sini Atla", required=False)

    image_url = forms.ChoiceField(label="Resim URL Sütunu (Örneğin: 'https://example.com/image.jpg')", required=False)
    skip_image_url = forms.BooleanField(label="Resim URL'sini Atla", required=False)

    def __init__(self, excel_columns, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(col, col) for col in excel_columns]
        # Set choices for all fields
        for idx, field_name in enumerate(['exam_type', 'exam_year', 'question_number', 'subject', 'correct_answer', 'achievement_code', 'difficulty_level', 'video_solution_url', 'image_url']):
            if field_name in self.fields:
                self.fields[field_name].choices = choices
                # Set initial selection to the corresponding column
                if idx < len(excel_columns):
                    self.fields[field_name].initial = excel_columns[idx]

class QuestionForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False, label='DigitalOcean Depolamaya Yükle')

    class Meta:
        model = Question
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get('upload_image')

        if image:
            # Upload to DigitalOcean Spaces
            session = boto3.session.Session()
            client = session.client(
                's3',
                region_name=os.getenv('DO_SPACES_REGION'),
                endpoint_url=os.getenv('DO_SPACES_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('DO_SPACES_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('DO_SPACES_SECRET_KEY'),
            )
            # Generate a unique filename using UUID
            filename = f"question-images/others/{uuid.uuid4()}.png"
            client.put_object(
                Bucket=os.getenv('DO_SPACES_NAME'),
                Key=filename,
                Body=image,
                ContentType=image.content_type,
                ACL='public-read'
            )
            # Use the CDN endpoint for better performance
            instance.image_url = f"{os.getenv('DO_SPACES_SUBDOMAIN')}/{filename}"

        if commit:
            instance.save()
        return instance

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm

    list_display = (
        'id',
        'question_number', 
        'exam_year', 
        'exam_type', 
        'subject', 
        'topic', 
        'correct_answer', 
        'image_preview',
        'difficulty_level', 
    )
    list_filter = (
        ('exam_year', RelatedDropdownFilter),
        ('exam_type', RelatedDropdownFilter),
        ('subject', RelatedDropdownFilter),
        ('topic', RelatedDropdownFilter),
        ('difficulty_level', DropdownFilter),
    )
    search_fields = ('exam_year__year', 'exam_type__name', 'subject__name', 'topic__name')
    ordering = ('exam_year', 'exam_type', 'subject', 'topic', 'question_number')
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('exam_year', 'exam_type', 'subject', 'topic', 'question_number')
        }),
        ('Detaylar', {
            'fields': ('correct_answer', 'difficulty_level')
        }),
        ('Medya', {
            'fields': ('upload_image', 'image_url', 'video_solution_url', 'image_display')
        }),
    )

    readonly_fields = ('image_display',)  # Make the image preview readonly

    list_per_page = 10  # Reduce the number of records per page
    change_list_template = "admin/questions/question_changelist.html"

    class Media:
        """Inject custom JavaScript into the admin change page."""
        js = ('js/image_confirmation.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['upload_image'].widget.attrs.update({'style': 'margin-bottom: 10px;'})
        return form

    def image_display(self, obj):
        """Render the image preview directly in full size."""
        if obj.image_url:
            return mark_safe(
                f'''
                <div style="overflow: auto; width: 50%; max-width: 50%; margin-top: 10px;">
                    <img src="{obj.image_url}" 
                         style="max-width: 100%; height: auto; display: block; margin: auto;" />
                </div>
                '''
            )
        return "Görsel Yok"

    def image_preview(self, obj):
        if obj.image_url:
            return mark_safe(
                f'''
                <a href="{obj.image_url}" target="_blank">
                    <img src="{obj.image_url}" 
                        style="max-width: 100px; max-height: 100px; object-fit: contain; display: block; margin: auto; transition: transform 0.3s ease;" />
                </a>
                <style>
                    a img:hover {{
                        position: relative;
                        z-index: 999;
                        transform: scale(3.5);  /* Enlarge the image on hover */
                        max-width: none;
                        max-height: none;
                        width: auto;
                        height: auto;
                        object-fit: contain;  /* Ensure the whole image is visible */
                        transition: transform 0.3s ease;  /* Smooth transition */
                    }}
                </style>
                '''
            )
        return "Görsel Yok"

    image_preview.short_description = "Görsel Önizleme"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.admin_site.admin_view(self.upload_excel), name='questions_upload_excel'),
            path('upload-excel/column-mapping/', self.admin_site.admin_view(self.column_mapping), name='questions_column_mapping'),
                path('upload-history/', self.admin_site.admin_view(lambda request: upload_history(request, 'questions')), name='upload_history'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['check_task_status_url'] = reverse('check_task_status', args=['questions'])
        extra_context['history_url'] = reverse('upload_history', args=['questions'])  # Ensure 'questions' is passed here
        return super().changelist_view(request, extra_context=extra_context)

    def upload_excel(self, request):
        if request.method == 'POST':
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                self.message_user(request, "Herhangi bir dosya yüklenmedi.", level=messages.ERROR)
                return redirect('..')

            try:
                # Read the Excel file using pandas
                df = pd.read_excel(excel_file, engine='openpyxl')
                request.session['uploaded_data'] = df.to_dict(orient='list')  # Store data in session
                request.session['excel_columns'] = list(df.columns)  # Store column names in session
                return redirect('admin:questions_column_mapping')  # Redirect to column mapping
            except Exception as e:
                self.message_user(request, f"Bir hata oluştu: {e}", level=messages.ERROR)
                return redirect('..')

        form = QuestionUploadForm()
        return render(request, 'admin/questions/upload_excel.html', {'form': form})

    def column_mapping(self, request):
        excel_columns = request.session.get('excel_columns', None)
        df_data = request.session.get('uploaded_data', None)
        if not excel_columns or not df_data:
            self.message_user(request, "Excel verisi bulunamadı. Lütfen tekrar yükleyin.", level=messages.ERROR)
            return redirect('admin:upload-excel')

        if request.method == 'POST':
            form = ColumnMappingForm(excel_columns, request.POST)
            if form.is_valid():
                try:
                    # Pass data to the Celery task
                    task = process_bulk_upload_questions.delay(df_data, form.cleaned_data)
                    request.session['last_task_id'] = task.id
                    self.message_user(request, "Veriler işlenmek üzere sıraya alındı. Durumu kontrol etmek için 'Yükleme Durumunu Kontrol Et' butonuna basın.", level=messages.SUCCESS)
                    return redirect('../..')
                except Exception as e:
                    self.message_user(request, f"Hata oluştu: {e}", level=messages.ERROR)
                    return redirect('..')
        else:
            form = ColumnMappingForm(excel_columns)
        return render(request, 'admin/questions/column_mapping.html', {'form': form})
