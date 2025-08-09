from django.shortcuts import render

def paytr_success_view(request):
    return render(request, 'payment_successful.html')

def paytr_failed_view(request):
    return render(request, 'payment_failed.html')
