"""
URL configuration for reloudAPI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from api import views
from django.conf import settings
from django.conf.urls.static import static




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', views.userList),
    path('api/user/audios/', views.getAllAudio),
    path('api/user/signup/', views.createUser, name='signup'),
    path('api/session/', views.sessions, name='sessions'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/convert/', views.convertVideo, name='convert'),
    path('api/audio/', views.audio),
    path('api/audio/<int:id>/', views.audio),
    path('api/audio/<str:name>/', views.getAudioByName)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
