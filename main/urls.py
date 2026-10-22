from django.contrib.auth import views as auth_views
from django.urls import path
from . import seguransa, views

urlpatterns = [
	path('', views.home, name='home'),
	path('login/', views.LoginTap.as_view(), name='login'),
	path('logout/', auth_views.LogoutView.as_view(), name='logout'),
	path('login/2fa/', seguransa.login_2fa, name='login-2fa'),
	path('seguransa/2fa/', seguransa.seguransa_2fa, name='seguransa-2fa'),
	path('seguransa/sai-hotu/', seguransa.sai_hotu, name='sai-hotu'),
	path('password/', views.PasswordTroka.as_view(), name='change-password'),
	path('password/done/', auth_views.PasswordChangeDoneView.as_view(
		template_name='auth/change_password_done.html'), name='password_change_done'),
]
