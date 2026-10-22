from django.contrib.auth.models import User
from django.db import models
from config.utils import hash_id


class HashedModel(models.Model):
	"""Model dasar dengan kolom hashed (HMAC-SHA256) yang terisi otomatis setelah id ada."""
	hashed = models.CharField(max_length=64, null=True, blank=True, editable=False)

	class Meta:
		abstract = True

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if not self.hashed:
			self.hashed = hash_id(f'{self._meta.label}:{self.pk}')
			super().save(update_fields=['hashed'])


class LoginLog(models.Model):
	"""Rejistu tentativa login (susesu, sala, bloku, 2FA) ba auditoria seguransa."""
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	username = models.CharField(max_length=150, blank=True)
	ip = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=200, blank=True)
	hasil = models.CharField(max_length=15)
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-datetime', '-id']
		indexes = [models.Index(fields=['username', 'datetime'])]

	def __str__(self):
		template = '{0.datetime:%Y-%m-%d %H:%M} {0.username} {0.hasil}'
		return template.format(self)


class LoginTentativa(models.Model):
	"""Kontador tentativa sala ba kombinasaun username + IP (iha database: seguru ba worker barak)."""
	xave = models.CharField(max_length=255, unique=True)
	gagal = models.PositiveSmallIntegerField(default=0)
	ikus = models.DateTimeField()
	bloku_to = models.DateTimeField(null=True, blank=True)


class Totp(models.Model):
	"""Autentikasaun rua faktór (TOTP RFC 6238) ba uzuáriu."""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='totp')
	secret = models.CharField(max_length=64)
	aktivu = models.BooleanField(default=False)
	ultimu_step = models.BigIntegerField(default=0)      # proteje replay: kódigu ida uza dala ida deit
	datetime = models.DateTimeField(auto_now=True)


class KodeRekupera(models.Model):
	"""Kódigu rekuperasaun (uza dala ida) se perde telemovel 2FA."""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kode_rekupera')
	hash = models.CharField(max_length=64)
	usadu = models.BooleanField(default=False)
