from django.contrib.auth.models import User
from django.db import models


class Notifikasaun(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifikasaun')
	mesaun = models.CharField(max_length=200, verbose_name="Mensajen")
	url = models.CharField(max_length=200, blank=True)
	is_read = models.BooleanField(default=False)
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-datetime', '-id']

	def __str__(self):
		template = '{0.user} - {0.mesaun}'
		return template.format(self)
