from django.http import HttpResponse

def ads_txt(request):
    content = "google.com, pub-3709370249567382, DIRECT, f08c47fec0942fa0"
    return HttpResponse(content, content_type="text/plain")
