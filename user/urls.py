from django.urls import path
from . import views

urlpatterns = [
	path('', views.UserList, name='user-list'),
	path('add/', views.UserAdd, name='user-add'),
	path('<int:pk>/edit/', views.UserUpdate, name='user-update'),
	path('<int:pk>/reset/', views.UserResetPassword, name='user-reset'),
	path('<int:pk>/reset-2fa/', views.UserReset2fa, name='user-reset-2fa'),
	path('log/', views.UserLog, name='user-log'),
]
