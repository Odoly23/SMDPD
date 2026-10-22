from django.contrib.auth.models import User
from django.db import models
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun
from membro.models import Membro

TIPU = [('Reuniaun', 'Reuniaun'), ('Formasaun', 'Formasaun'), ('Kongresu', 'Kongresu / Konferénsia'), ('Kampaña', 'Kampaña'),
	('Sosiál', 'Aktividade Sosiál'), ('Seluk', 'Seluk')]
ESTADU = [('Prezente', 'Prezente'), ('Lisensa', 'Lisensa'), ('Falta', 'Falta')]
SCOPE_FIELDS = ['departamentu', 'organizasaun', 'aldeia', 'village', 'post', 'municipality']


class Eventu(models.Model):
	"""Eventu partidu (reuniaun, formasaun, kongresu...) ho lista prezensa. Área eventu = área ema ne'ebé kria."""
	titulu = models.CharField(max_length=150, verbose_name="Títulu")
	tipu = models.CharField(choices=TIPU, max_length=15, default='Reuniaun', verbose_name="Tipu")
	data_hahu = models.DateTimeField(verbose_name="Data/Oras Hahu")
	data_remata = models.DateTimeField(null=True, blank=True, verbose_name="Data/Oras Remata")
	fatin = models.CharField(max_length=150, blank=True, verbose_name="Fatin")
	deskrisaun = models.TextField(blank=True, verbose_name="Deskrisaun")
	municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	post = models.ForeignKey(AdministrativePost, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	village = models.ForeignKey(Village, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	organizasaun = models.ForeignKey(Organizasaun, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	departamentu = models.ForeignKey(Departamentu, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
	kria_husi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data_hahu']

	def unidade(self):
		for k in SCOPE_FIELDS:
			v = getattr(self, k)
			if v:
				return v
		return 'PLP Nasionál'

	def __str__(self):
		template = '{0.titulu}'
		return template.format(self)


class Prezensa(models.Model):
	eventu = models.ForeignKey(Eventu, on_delete=models.CASCADE, related_name='prezensa')
	membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='prezensa')
	estadu = models.CharField(choices=ESTADU, max_length=10, default='Prezente')
	nota = models.CharField(max_length=150, blank=True)
	rejistu_husi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	datetime = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = [('eventu', 'membro')]
		ordering = ['membro__nome']

	def __str__(self):
		template = '{0.eventu} - {0.membro}: {0.estadu}'
		return template.format(self)
