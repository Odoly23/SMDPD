from django.contrib.auth.models import User
from django.db import models
from custom.models import Municipality, Departamentu, Organizasaun

AUDIENS = [('Hotu', 'Hotu (PLP tomak)'), ('Munisipiu', 'Munisipiu ida'), ('Organizasaun', 'Orgaun/Movimentu ida'), ('Departamentu', 'Departamentu ida')]


class Anunsiu(models.Model):
	"""Anunsiu/komunikadu husi lideransa ba membru ho login iha área ka unidade espesífiku."""
	titulu = models.CharField(max_length=150, verbose_name="Títulu")
	mensagem = models.TextField(verbose_name="Mensajen")
	audiens = models.CharField(choices=AUDIENS, max_length=15, default='Hotu', verbose_name="Ba sé")
	municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Munisipiu")
	organizasaun = models.ForeignKey(Organizasaun, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Orgaun/Movimentu")
	departamentu = models.ForeignKey(Departamentu, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Departamentu")
	importante = models.BooleanField(default=False, verbose_name="Importante (hatudu iha leten)")
	data_remata = models.DateField(null=True, blank=True, verbose_name="Validu to'o")
	kria_husi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-importante', '-datetime']

	def alvu(self):
		return {'Hotu': 'PLP tomak', 'Munisipiu': self.municipality, 'Organizasaun': self.organizasaun,
			'Departamentu': self.departamentu}.get(self.audiens)

	def __str__(self):
		template = '{0.titulu}'
		return template.format(self)
