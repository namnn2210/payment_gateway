from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language


urlpatterns = [
    path('', include('cms.urls')),
    path('admin/', admin.site.urls),
    path('bank/', include('bank.urls')),
    path('payout/', include('payout.urls')),
    path('settle/', include('settle_payout.urls')),
    path('acb/', include('acb.urls')),
    path('partner/', include('partner.urls')),
    path('notifications/', include('notification.urls')),
    path('employee/', include('employee.urls')),
    path('report/', include('report.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
