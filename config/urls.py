"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf.urls.i18n import i18n_patterns
# from usermodel.views import GoogleLogin
# admin.site.index_template = 'admin_interface/custom.html'
# admin.autodiscover()
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns # new
from django.views.static import serve
from django.views.generic.base import TemplateView

urlpatterns = ([
    # re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    # re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    # path("i18n/", include("django.conf.urls.i18n")),
    path('Pickle_R@ise03/', admin.site.urls),
    path('', include('home.urls')),
    path('cities/', include('cities.urls')),
    path('api/cities/', include('cities.api_urls')),
    path('options/', include('options.urls')),
    path('api/options/', include('options.api_urls')),    
    path('prices/', include('prices.urls')),
    path('api/prices/', include('prices.api_urls')),
    path('orders/', include('order.urls')),
    path('api/orders/', include('order.api_urls')),    
    path('cart/', include('cart.urls')),
    path('users/', include('usermodel.urls')),
    path('profile/', include('userprofile.urls')),
    path('account/', include('allauth.urls')),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('address/', include('address_note.urls')),
    path('payment/', include('payment.api_urls')),
    path('asset/', include('payment.urls')),
    path('business/', include('business.urls')),
    path('blogs/', include('blog.urls')),   
    path('factor/', include('factor.urls')),
    path('dispatcher/', include('dispatcher.urls')),
    path('dispatcher/order/', include('dispatcher_order.urls')),
    path('dispatcher/profile/', include('dispatcher_profile.urls')),
    path('dispatcher/vehicle/', include('dispatcher_vehicle.urls')),
    path('dispatcher/payment/', include('dispatcher_payment.urls')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    #apikey
    path('apikey/', include('apikey.urls')),
    #admin
    path('admin/order/', include('order.admin_urls')),
    path('admin/business/', include('business.admin_urls')),
    path('admin/options/', include('options.admin_urls')),
    path('admin/dispatchers/', include('dispatcher_profile.admin_urls')),
    # robots.txt path below
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("core/", include("core.urls")),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
])
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# urlpatterns += i18n_patterns(path("admin/", admin.site.urls))
