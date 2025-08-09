from django.http import JsonResponse
from others.models import BulkUploadStatus
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

def check_task_status(request, task_type):
    task_id = request.session.get('last_task_id')
    if not task_id:
        return JsonResponse({'status': 'NO_TASK', 'message': 'Herhangi bir işlem bulunamadı.'})

    task_status = BulkUploadStatus.objects.filter(task_type=task_type).order_by('-id').first()
    
    if task_status is None:
        return JsonResponse({'status': 'NOT_FOUND', 'message': 'İşlem bulunamadı.'})

    return JsonResponse({
        'status': task_status.status,
        'message': task_status.message,
        'progress': task_status.progress
    })

def upload_history(request, task_type):
    # Get all upload history for the given task type (e.g., 'questions' or 'uni_rankings')
    uploads = BulkUploadStatus.objects.filter(task_type=task_type).order_by('-created_at')

    # Set up pagination (10 entries per page as an example)
    paginator = Paginator(uploads, 10)  # Show 10 uploads per page
    page = request.GET.get('page')

    try:
        uploads_paginated = paginator.page(page)
    except PageNotAnInteger:
        uploads_paginated = paginator.page(1)  # If page is not an integer, deliver first page.
    except EmptyPage:
        uploads_paginated = paginator.page(paginator.num_pages)  # If page is out of range, deliver last page.

    return render(request, 'admin/upload_history.html', {
        'uploads': uploads_paginated,
        'task_type': task_type,
    })

def upload_history_details(request, upload_id):
    try:
        upload = BulkUploadStatus.objects.get(id=upload_id)
        data = {
            'message': upload.message,
            'status': upload.status,
            'user': upload.user.email if upload.user else 'Bilinmeyen Kullanıcı',  # Check if user is None
            'created_at': upload.created_at.strftime("%d %B %Y %H:%M")
        }
        print("data", data)
        return JsonResponse(data)
    except BulkUploadStatus.DoesNotExist:
        return JsonResponse({'error': 'Yükleme bulunamadı.'}, status=404)

def base_view(request):
    return render(request, 'base.html')

def question_redirect_view(request, question_code):
    return render(request, 'soru.html', {'question_code': question_code})
