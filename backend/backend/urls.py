"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from backend import settings
from django.conf.urls.static import static
from move_on.views import get_energy, start_walk, update_walk, finish_walk, walk_history, tasks_complete, \
    get_statistics, track_data, log_js_errors, update_walk_session, end_walk, stop_walk
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.urls import get_resolver


schema_view = get_schema_view(
    openapi.Info(
        title="MoveOn API",
        default_version='v1',
        description="API для управления прогулками, заданиями и статистикой.",
    ),
    public=True,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('energy/<int:telegram_id>/', get_energy, name='get_energy'),
    path('walk/start/', start_walk, name='start_walk'),
    path('walk/update/', update_walk, name='update_walk'),
    path('walk/finish/', finish_walk, name='finish_walk'),
    path('walk/history/<int:telegram_id>/', walk_history, name='walk_history'),
    path('tasks/complete/', tasks_complete, name='tasks_complete'),
    path('statistics/<int:telegram_id>/', get_statistics, name='get_statistics'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs.<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-formatted'),

    path('webapp-test/', TemplateView.as_view(template_name='webapp_test.html')),

    # API для работы с данными сенсоров и прогулками
    path('api/track-data/', track_data, name='track_data'),
    # path('api/process-data/', process_sensor_data, name='process_data'),
    path('api/update-walk-session/', update_walk_session, name='update_walk_session'),
    path('api/end-walk/', end_walk, name='end_walk'),
    path('api/stop-walk/', stop_walk, name='stop_walk'),
    path('api/start-walk/', start_walk, name='start_walk'),

    # Логи для JS
    path('log_js_errors/', log_js_errors, name='js_logs_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
