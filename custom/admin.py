from django.contrib import admin
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun

for model in (Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun):
	admin.site.register(model)
