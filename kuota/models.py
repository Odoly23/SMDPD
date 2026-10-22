from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from membro.models import Membro

METODU = [('Kontante', 'Osan kontante'), ('Transfere', 'Transferénsia banku'), ('Mobile', 'Mobile money'), ('Seluk', 'Seluk')]


class Kuota(models.Model):
	"""Kuota/kontribuisaun membru (USD) ba tinan ida. Membru bele selu dala barak iha tinan ida."""
	membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='kuota', verbose_name="Membru")
	tinan = models.PositiveSmallIntegerField(verbose_name="Tinan")
	montante = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Montante (USD)")
	data_selu = models.DateField(verbose_name="Data Selu")
	metodu = models.CharField(choices=METODU, max_length=10, default='Kontante', verbose_name="Métodu")
	nota = models.CharField(max_length=150, blank=True, verbose_name="Nota")
	rejistu_husi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data_selu', '-id']

	def __str__(self):
		template = '{0.membro} {0.tinan}: {0.montante}'
		return template.format(self)
