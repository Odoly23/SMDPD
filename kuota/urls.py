from django.urls import path
from . import views

urlpatterns = [
	path('', views.KuotaList, name='kuota-list'),
	path('add/', views.KuotaAdd, name='kuota-add'),
	path('search/', views.KuotaSearch, name='kuota-search'),
	path('rezumu/', views.KuotaRezumu, name='kuota-rezumu'),
	path('<int:pk>/del/', views.KuotaDel, name='kuota-del'),
]
