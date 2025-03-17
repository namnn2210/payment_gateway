from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .api_docs import api_root

# Traditional web application URLs
web_urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('cms.urls')),
    path('bank/', include('bank.urls')),
    path('payout/', include('payout.urls')),
    path('settle/', include('settle_payout.urls')),
    path('acb/', include('acb.urls')),
    path('partner/', include('partner.urls')),
    path('employee/', include('employee.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
)

# API URLs
api_urlpatterns = [
    # API documentation
    path('api/', api_root, name='api-root'),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints for each app
    path('api/bank/', include('bank.api.urls')),
    path('api/payout/', include('payout.api.urls')),
    path('api/settle/', include('settle_payout.api.urls')),
    path('api/acb/', include('acb.api.urls')),
    path('api/partner/', include('partner.api.urls')),
    path('api/employee/', include('employee.api.urls')),
]

# Combine all URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns

# Additional URL patterns
urlpatterns += [
    path('set_language/', set_language, name='set_language'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
