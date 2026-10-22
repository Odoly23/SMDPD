from django.db import models
from config.models import HashedModel
from config.upload_utils import upload_logo, validate_image_size


class Municipality(models.Model):
	code = models.CharField(max_length=5, null=True, blank=True, verbose_name="Kódigu")
	name = models.CharField(max_length=100, verbose_name="Naran Munisipiu")
	hckey = models.CharField(max_length=10, blank=True, default="", verbose_name="Xave Mapa (Highcharts)")

	class Meta:
		ordering = ['name']

	def __str__(self):
		template = '{0.name}'
		return template.format(self)


class AdministrativePost(models.Model):
	code = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name="Kódigu")
	municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, verbose_name="Munisipiu")
	name = models.CharField(max_length=100, verbose_name="Naran Postu")

	class Meta:
		ordering = ['municipality__name', 'name']

	def __str__(self):
		template = '{0.name}'
		return template.format(self)


class Village(models.Model):
	code = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name="Kódigu")
	administrativepost = models.ForeignKey(AdministrativePost, on_delete=models.CASCADE, verbose_name="Postu")
	name = models.CharField(max_length=100, verbose_name="Naran Suku")

	class Meta:
		ordering = ['name']

	def __str__(self):
		template = '{0.name}'
		return template.format(self)


class Aldeia(models.Model):
	code = models.CharField(max_length=30, unique=True, null=True, blank=True, verbose_name="Kódigu")
	village = models.ForeignKey(Village, on_delete=models.CASCADE, verbose_name="Suku")
	name = models.CharField(max_length=100, verbose_name="Naran Aldeia")

	class Meta:
		ordering = ['village__name', 'name']

	def __str__(self):
		template = '{0.name}'
		return template.format(self)


class Departamentu(HashedModel):
	"""Departamentu iha Estrutura Nasionál ka iha Orgaun/Movimentu ida (ez. Finansas, Informasaun)."""
	organizasaun = models.ForeignKey("Organizasaun", on_delete=models.PROTECT, null=True, blank=True, related_name="departamentu_set", verbose_name="Orgaun/Movimentu")
	code = models.CharField(max_length=10, verbose_name="Kódigu")
	name = models.CharField(max_length=100, verbose_name="Naran")
	is_active = models.BooleanField(default=True, verbose_name="Ativu")

	class Meta:
		ordering = ['name']

	def __str__(self):
		if self.organizasaun_id:
			return '{0.name} ({0.organizasaun.code})'.format(self)
		return self.name


class Organizasaun(HashedModel):
	"""Orgaun/Movimentu ne'ebé hela iha partidu laran (ez. Movimentu Diaspora, Sentru Estudu Estratejiku)."""
	code = models.CharField(max_length=10, verbose_name="Kódigu")
	name = models.CharField(max_length=100, verbose_name="Naran")
	logo = models.ImageField(upload_to=upload_logo, null=True, blank=True, verbose_name="Logo", validators=[validate_image_size])
	is_active = models.BooleanField(default=True, verbose_name="Ativu")

	class Meta:
		ordering = ['name']

	def __str__(self):
		template = '{0.name}'
		return template.format(self)
