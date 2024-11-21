"""
URL configuration for drfsite project.

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
from django.urls import include, path
from django.contrib import admin
from maker.views import ChangePasswordView, CustomTokenObtainPairView, LinkView, CollectionView, PasswordResetConfirmView, PasswordResetView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Link Management API",
        default_version='v1',
        description="API для управления ссылками и коллекциями",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
        path('auth/password-reset/', PasswordResetView.as_view(), name='password-reset'),
        path('auth/reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
        path('links/', LinkView.as_view(), name='link-list'),
        path('links/<int:pk>/', LinkView.as_view(), name='link-detail'),
        path('collections/', CollectionView.as_view(), name='collection-list'),
        path('collections/<int:pk>/', CollectionView.as_view(), name='collection-detail'),
    ])),
]
