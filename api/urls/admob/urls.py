from django.urls import path
from admob.views.admob_views import ads_txt

urlpatterns = [
    path('app-ads.txt', ads_txt, name='app-ads'),
]
