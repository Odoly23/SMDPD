from django.contrib.auth.models import User
from django.db import models
from membro.models import Membro
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun


class UserScope(models.Model):
	"""Área ka unidade ne'ebé user bele hare (selae peran Nasionál ne'ebé hare hotu)."""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='scope')
	municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Munisipiu")
	post = models.ForeignKey(AdministrativePost, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Postu Administrativu")
	village = models.ForeignKey(Village, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Suku")
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Aldeia")
	departamentu = models.ForeignKey(Departamentu, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Departamentu")
	organizasaun = models.ForeignKey(Organizasaun, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Orgaun/Movimentu")

	membro = models.OneToOneField(Membro, on_delete=models.SET_NULL, null=True, blank=True, related_name='login', verbose_name="Membru")

	def __str__(self):
		template = '{0.user}'
		return template.format(self)
