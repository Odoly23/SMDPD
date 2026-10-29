from django.urls import path
from . import views

urlpatterns = [
	path('', views.MembroList, name='membro-list'),
	path('add/', views.MembroAdd, name='membro-add'),
	path('search/', views.MembroSearch, name='membro-search'),
	path('import/', views.MembroImport, name='membro-import'),
	path('import/modelu/', views.MembroImportTemplate, name='membro-import-template'),
	path('aprovasaun/', views.AprovasaunList, name='aprovasaun-list'),
	path('aprovasaun/bulk/', views.AprovasaunBulk, name='aprovasaun-bulk'),
	path('aprovasaun/<str:hashid>/aprova/', views.AprovasaunAprova, name='aprovasaun-aprova'),
	path('aprovasaun/<str:hashid>/rejeita/', views.AprovasaunRejeita, name='aprovasaun-rejeita'),
	path('struktura/', views.StrukturaPainel, name='struktura-painel'),
	path('struktura/<str:nivel>/', views.StrukturaList, name='struktura-list'),
	path('alokasaun/add/', views.AlokasaunAdd, name='alokasaun-add'),
	path('alokasaun/<int:pk>/edit/', views.AlokasaunUpdate, name='alokasaun-update'),
	path('alokasaun/<int:pk>/del/', views.AlokasaunDel, name='alokasaun-del'),
	path('alokasaun/<int:pk>/login/', views.LoginKria, name='login-kria'),
	path('historia/', views.HistoriaList, name='historia-list'),
	path('<str:hashid>/', views.MembroDetail, name='membro-detail'),
	path('<str:hashid>/fotu/', views.MembroFotu, name='membro-fotu'),
	path('<str:hashid>/kartaun/', views.MembroKartaun, name='membro-kartaun'),
	path('<str:hashid>/edit/', views.MembroUpdate, name='membro-update'),
	path('<str:hashid>/del/', views.MembroDel, name='membro-del'),
]
