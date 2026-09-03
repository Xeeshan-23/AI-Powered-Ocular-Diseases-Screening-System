"""
URL configuration for ocular_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('screening/', views.screening_view, name='screening'),
    path('history/', views.history_view, name='history'),
    path('specialists/', views.specialists_view, name='specialists'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('chatbot/', views.chatbot_page, name='chatbot_page'), # The new page
    path('chatbot-api/', views.get_chatbot_response, name='chatbot_api'), # The API logic
    path('delete-chat/<int:session_id>/', views.delete_chat_session, name='delete_chat'),
    path('download-report/<int:screening_id>/', views.download_screening_pdf, name='download_pdf'), 
    path('feedback/', views.submit_feedback, name='submit_feedback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)