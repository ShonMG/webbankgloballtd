from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.index, name='index'),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts-amor108/', include('accounts_amor108.urls')),
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
    path('pools/', include('pools.urls')),
    path('contributions/', include('contributions.urls')),
    path('payments/', include('payments.urls')),
    path('profits/', include('profits.urls')),
    path('governance/', include('governance.urls')), # New: Include governance app URLs
    path('audit/', include('audit.urls')),
    path('webbankboard/', include('webbankboard.urls')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)