from django.urls import path
from ogmmateryal.views.ogmmateryal_views import YKSPuanHesaplamaView

urlpatterns = [
    path('yks-ranking-calculation/', YKSPuanHesaplamaView.as_view(), name='yks-ranking-calculation'),
]