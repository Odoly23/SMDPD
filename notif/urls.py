from django.urls import path
from . import views

urlpatterns = [
	path('', views.NotifList, name='notif-list'),
	path('le/', views.NotifLe, name='notif-le'),
	path('<int:pk>/loke/', views.NotifLoke, name='notif-loke'),
]
