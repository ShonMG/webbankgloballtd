from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.index, name='index'),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('shares/', include('shares.urls')),
    path('loans/', include('loans.urls')),
    path('guarantees/', include('guarantees.urls')),
    path('members/', include('members.urls')),
    path('directors/', include('directors.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('support/', include('support.urls')),
    path('notifications/', include('notifications.urls')),
    path('profiles/', include('profiles.urls')),
    path('messaging/', include('messaging.urls')),
    path('amor108/', include('amor108.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)