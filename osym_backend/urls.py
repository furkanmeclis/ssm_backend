from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.urls import include
from others.views.other_views import base_view

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/v1/', include('api.urls.users.urls')),
    path('api/v1/', include('api.urls.exams.urls')),
    path('api/v1/', include('api.urls.grades.urls')),
    path('api/v1/', include('api.urls.questions.urls')),
    path('api/v1/', include('api.urls.quizzes.urls')),
    path('api/v1/', include('api.urls.ogmmateryal.urls')),
    path('api/v1/', include('api.urls.reports.urls')),
    path('api/v1/', include('api.urls.uni_rankings.urls')),
    path('api/v1/', include('api.urls.others.urls')),
    path('api/v1/', include('api.urls.paytr.urls')),
    path('api/v1/', include('api.urls.topic_history.urls')),

    path('api/v1.1/', include('api.urls.users.v1_1_urls')),

    path('api/v2/', include('api.urls.quizzes.v2_urls')),
    path('api/v2/', include('api.urls.exam_sets.v2_urls')),
    path('api/v2/', include('api.urls.ai.v2_urls')),
    path('api/v2/', include('api.urls.users.v2_urls')),
    path('api/v2/', include('api.urls.metrics.v2_urls')),
    path('api/v2/', include('api.urls.questions.v2_urls')),
    path('', include('api.urls.admob.urls')),
    path('', include('api.urls.others.urls')),
]

excluded_pattern = '|'.join(settings.EXCLUDED_CATCH_ALL_PREFIXES)
negative_lookahead = f'(?!({excluded_pattern}))'

urlpatterns += [
    re_path(f'^{negative_lookahead}.*$', base_view, name='catch_all'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
