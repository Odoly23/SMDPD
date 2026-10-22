from django.urls import path
from . import views

urlpatterns = [
	path('', views.AnunsiuList, name='anunsiu-list'),
	path('add/', views.AnunsiuAdd, name='anunsiu-add'),
	path('<int:pk>/edit/', views.AnunsiuUpdate, name='anunsiu-update'),
	path('<int:pk>/del/', views.AnunsiuDel, name='anunsiu-del'),
]
