from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from .models import Program, Location
from .tasks import process_bulk_upload_uni_rankings
from others.models import BulkUploadStatus
from django.urls import reverse
import pandas as pd
import re

class UniversityProgramUploadForm(forms.Form):
    excel_file = forms.FileField()

class ColumnMappingForm(forms.Form):
    # Required fields
    exam_year = forms.CharField(label="Sınav Yılı (Örneğin: '2024')", required=True)
    university_name = forms.ChoiceField(label="Üniversite ve Bölüm İsimleri Sütunu (Örneğin: 'Boğaziçi Üniversitesi')", required=True)
    
    # Optional fields with a skip checkbox
    program_code = forms.ChoiceField(label="Program Kodu Sütunu (Örneğin: '106510090')", required=False)
    skip_program_code = forms.BooleanField(label="Program Kodunu Atla", required=False)

    ranking = forms.ChoiceField(label="Sıralama Sütunu (Örneğin: '24014')", required=False)
    skip_ranking = forms.BooleanField(label="Sıralamayı Atla", required=False)

    min_score = forms.ChoiceField(label="En Küçük Puan Sütunu (Örneğin: '339.9075')", required=False)
    skip_min_score = forms.BooleanField(label="En Küçük Puanı Atla", required=False)
    
    max_score = forms.ChoiceField(label="En Büyük Puan Sütunu (Örneğin: '439.9075')", required=False)
    skip_max_score = forms.BooleanField(label="En Büyük Puanı Atla", required=False)
    
    program_type = forms.ChoiceField(label="Puan Türü Sütunu (Örneğin: 'SAY')", required=False)
    skip_program_type = forms.BooleanField(label="Puan Türünü Atla", required=False)
    
    education_length = forms.ChoiceField(label="Öğrenim Süresi Sütunu (Örneğin: '4')", required=False)
    skip_education_length = forms.BooleanField(label="Eğitim Süresini Atla", required=False)

    def __init__(self, excel_columns, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Normalize and clean column names: strip spaces, remove line breaks, and extra whitespace
        def clean_column_name(col):
            return re.sub(r'\s+', ' ', col).strip()
        
        cleaned_columns = [(clean_column_name(col), clean_column_name(col)) for col in excel_columns if isinstance(col, str)]
        
        # Set choices for all fields
        for field_name in ['university_name', 'program_code', 'education_length', 
                           'program_type', 'ranking', 'min_score', 'max_score']:
            if field_name in self.fields:
                self.fields[field_name].choices = cleaned_columns

class ProgramAdmin(admin.ModelAdmin):
    list_display = ('major', 'university', 'exam_year')
    search_fields = ('major__name', 'university__name', 'exam_year__year', 'program_code')
    change_list_template = "admin/uni_rankings/major_changelist.html"
    list_per_page = 20  # Reduce the number of records per page

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.admin_site.admin_view(self.upload_excel), name='uni_rankings_upload_excel'),
            path('upload-excel/column-mapping/', self.admin_site.admin_view(self.column_mapping), name='uni_rankings_column_mapping'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Pass the task_type "questions" to the reverse function
        extra_context['check_task_status_url'] = reverse('check_task_status', args=['uni_rankings'])
        extra_context['history_url'] = reverse('upload_history', args=['uni_rankings'])  # Ensure 'uni_rankings' is passed here
        return super().changelist_view(request, extra_context=extra_context)

    def upload_excel(self, request):
        if request.method == 'POST':
            form = UniversityProgramUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                try:
                    # Read the Excel file
                    df = pd.read_excel(excel_file, engine='openpyxl')
                    request.session['uploaded_data'] = df.to_dict(orient='list')  # Store data in session
                    request.session['excel_columns'] = list(df.columns)  # Store column names in session
                    return redirect('admin:uni_rankings_column_mapping')  # Redirect to column mapping
                except Exception as e:
                    messages.error(request, f"Hata oluştu: {str(e)}")
                return redirect('..')

        form = UniversityProgramUploadForm()
        return render(request, 'admin/uni_rankings/upload_excel.html', {'form': form})

    def column_mapping(self, request):
        excel_columns = request.session.get('excel_columns', None)
        df_data = request.session.get('uploaded_data', None)
        if not excel_columns or not df_data:
            messages.error(request, "Excel verileri bulunamadı. Lütfen tekrar yükleyin.")
            return redirect('admin:upload-excel')

        if request.method == 'POST':
            # Clean the submitted data to remove extra spaces or line breaks
            cleaned_post = {key: re.sub(r'\s+', ' ', value).strip() if isinstance(value, str) else value 
                            for key, value in request.POST.items()}
            
            form = ColumnMappingForm(excel_columns, cleaned_post)
            if form.is_valid():
                try:
                    task = process_bulk_upload_uni_rankings.delay(df_data, form.cleaned_data)
                    request.session['last_task_id'] = task.id
                    messages.success(request, "Veriler işlenmek üzere sıraya alındı.")
                    return redirect('../..')
                except Exception as e:
                    messages.error(request, f"Hata oluştu: {str(e)}")
                    return redirect('../..')
            else:
                error_messages = [f"{field}: {error}" for field, errors in form.errors.items() for error in errors]
                messages.error(request, f"Form geçersiz. Hatalar: {', '.join(error_messages)}")
        else:
            form = ColumnMappingForm(excel_columns)
        return render(request, 'admin/uni_rankings/column_mapping.html', {'form': form})

admin.site.register(Program, ProgramAdmin)