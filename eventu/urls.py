from django.urls import path
from . import views

urlpatterns = [
	path('', views.EventuList, name='eventu-list'),
	path('add/', views.EventuAdd, name='eventu-add'),
	path('<int:pk>/', views.EventuDetail, name='eventu-detail'),
	path('<int:pk>/edit/', views.EventuUpdate, name='eventu-update'),
	path('<int:pk>/del/', views.EventuDel, name='eventu-del'),
	path('<int:pk>/prezensa/', views.PrezensaFoti, name='prezensa-foti'),
	path('<int:pk>/prezensa/rapidu/', views.PrezensaRapidu, name='prezensa-rapidu'),
	path('<int:pk>/prezensa/csv/', views.PrezensaCsv, name='prezensa-csv'),
]
