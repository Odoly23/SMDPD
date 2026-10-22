from django.urls import include, path
from . import views

urlpatterns = [
	path('', views.Dash, name='report-dash'),
	path('chart/', views.ChartDash, name='report-chart'),
	path('rekursu/', views.Rekursu, name='report-rekursu'),
	path('kualidade/', views.Kualidade, name='report-kualidade'),
	path('hamutuk/', views.MembroHamutuk, name='membro-hamutuk'),
	path('aniversariu/', views.Aniversariu, name='report-aniversariu'),
	path('api/', include('report.api.urls')),
]
