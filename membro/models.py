import datetime
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from config.models import HashedModel
from config.upload_utils import upload_foto, validate_image_size
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun

SEXU = [('Mane', 'Mane'), ('Feto', 'Feto')]
MARITAL = [('Solteiro/a', 'Solteiro/a'), ('Casado/a', 'Casado/a'), ('Divorciado/a', 'Divorciado/a'), ('Viuvo/a', 'Viuvo/a')]
STATUS = [('Ativu', 'Ativu'), ('Inativu', 'Inativu'), ('Falesidu', 'Falesidu')]
APROVASAUN = [('Pendente', 'Pendente'), ('Aprovadu', 'Aprovadu'), ('Rejeitadu', 'Rejeitadu')]

# Estrutura Nasionál (+ Departamentu), Munisipal, Postu Administrativu, Suku, Aldeia no Orgaun/Movimentu
NIVEL = [('Nasional', 'Nasionál'), ('Departamentu', 'Departamentu'), ('Munisipiu', 'Munisipal'), ('Postu', 'Postu Administrativu'),
	('Suku', 'Suku'), ('Aldeia', 'Aldeia'), ('Organizasaun', 'Orgaun/Movimentu')]
NIVEL_SLUG = {n.lower(): n for n, _ in NIVEL}

VICE_BARAK = ['Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Vice 5', 'Vice 6', 'Vice 7', 'Vice 8']  # Departamentu no Orgaun/Movimentu
POZISAUN_LIST = ['Presidente', 'Presidente Departamentu', 'Koordenador'] + VICE_BARAK + ['Sekretaria', 'Membru']
EDUKASAUN = [('SD', 'SD'), ('SMP', 'SMP'), ('SMA', 'SMA'), ('D3', 'D3'), ('Kandidatu S1', 'Kandidatu S1'), ('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3')]
POZISAUN = [(p, p) for p in POZISAUN_LIST]
POZISAUN_POR_NIVEL = {
	'Nasional': ['Presidente', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Membru'],
	'Departamentu': ['Presidente Departamentu', 'Koordenador'] + VICE_BARAK + ['Membru'],
	'Munisipiu': ['Koordenador', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Membru'],
	'Postu': ['Koordenador', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Membru'],
	'Suku': ['Koordenador', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Membru'],
	'Aldeia': ['Koordenador', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Membru'],
	'Organizasaun': ['Presidente'] + VICE_BARAK + ['Sekretaria', 'Koordenador', 'Membru'],
}
POZISAUN_BAIXA = 'Membru'  # pozisaun ne'ebé bele iha barak iha unidade ida


class Membro(HashedModel):
	nome = models.CharField(max_length=100, verbose_name="Naran")
	sex = models.CharField(choices=SEXU, max_length=6, verbose_name="Sexu")
	place_of_birth = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fatin Moris")
	date_of_birth = models.DateField(null=True, verbose_name="Data Moris")
	marital = models.CharField(choices=MARITAL, max_length=15, null=True, blank=True, verbose_name="Estado Civil")
	nu_eleitoral = models.CharField(max_length=30, unique=True, null=True, verbose_name="Nu. Eleitoral",
			validators=[RegexValidator(r'^[A-Za-z0-9\-/]{4,30}$', 'Deit letra, numeru, "-" no "/" (4 to 30 karakter).')])
	nu_bi = models.CharField(max_length=30, null=True, blank=True, verbose_name="Nu. BI")
	telefone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Nu. Telemovel",
			validators=[RegexValidator(r'^[0-9+\- ]{7,20}$', 'Nu. telemovel la loos.')])
	image = models.ImageField(upload_to=upload_foto, null=True, blank=True, verbose_name="Fotu",
			validators=[validate_image_size])
	municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, verbose_name="Munisipiu Rezidensia")
	post = models.ForeignKey(AdministrativePost, on_delete=models.PROTECT, null=True, verbose_name="Postu")
	village = models.ForeignKey(Village, on_delete=models.PROTECT, null=True, verbose_name="Suku")
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, verbose_name="Aldeia")
	address = models.CharField(max_length=150, null=True, blank=True, verbose_name="Hela Fatin")
	email = models.EmailField(null=True, blank=True, verbose_name="Email")
	nivel_edukasaun = models.CharField(choices=EDUKASAUN, max_length=20, null=True, blank=True, verbose_name="Nivel Estudu / Gelar")
	area_estudu = models.CharField(max_length=150, null=True, blank=True, verbose_name="Area Estudu")
	servisu_fatin = models.CharField(max_length=150, null=True, blank=True, verbose_name="Servisu Fatin Agora")
	esperensia = models.TextField(null=True, blank=True, verbose_name="Deskrisaun konaba Esperensia Servisu")
	kontribuisaun = models.TextField(null=True, blank=True, verbose_name="Kontribuisaun ba Programa PLP")
	municipality_orijin = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, blank=True, related_name='membro_orijin', verbose_name="Munisipiu Orijin")
	organizasaun = models.ForeignKey(Organizasaun, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Orgaun/Movimentu")
	data_hakbit = models.DateField(null=True, blank=True, verbose_name="Data Hakbit (Tama PLP)")
	status = models.CharField(choices=STATUS, max_length=10, default='Ativu', verbose_name="Status")
	aprovasaun = models.CharField(choices=APROVASAUN, max_length=10, default='Pendente', verbose_name="Aprovasaun")
	razaun_rejeita = models.TextField(null=True, blank=True, verbose_name="Razaun Rejeita")
	aprovadu_husi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	data_aprovasaun = models.DateTimeField(null=True, blank=True)
	datetime = models.DateTimeField(null=True)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

	class Meta:
		ordering = ['nome']

	def __str__(self):
		if not self.nu_eleitoral:
			return self.nome
		template = '{0.nome} ({0.nu_eleitoral})'
		return template.format(self)

	def kompletu(self):
		"""Dadus báziku kompletu (nu. eleitoral, data moris no área rezidénsia)."""
		return bool(self.nu_eleitoral and self.date_of_birth and self.aldeia_id)

	def age(self):
		if not self.date_of_birth:
			return None
		return int((datetime.date.today() - self.date_of_birth).days // 365.2425)


class Alokasaun(models.Model):
	"""Pozisaun/kargu membru iha struktura (Nasionál, Departamentu, Munisipal, Postu, Suku, Aldeia, Orgaun/Movimentu)."""
	membro = models.ForeignKey(Membro, on_delete=models.CASCADE, related_name='alokasaun', verbose_name="Membru")
	nivel = models.CharField(choices=NIVEL, max_length=15, verbose_name="Nivel")
	pozisaun = models.CharField(choices=POZISAUN, max_length=30, verbose_name="Pozisaun")
	departamentu = models.ForeignKey(Departamentu, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Departamentu")
	municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Munisipiu")
	post = models.ForeignKey(AdministrativePost, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Postu Administrativu")
	village = models.ForeignKey(Village, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Suku")
	aldeia = models.ForeignKey(Aldeia, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Aldeia")
	organizasaun = models.ForeignKey(Organizasaun, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Orgaun/Movimentu")
	data_hahu = models.DateField(verbose_name="Data Hahu")
	data_termina = models.DateField(null=True, blank=True, verbose_name="Data Termina")
	ativu = models.CharField(choices=[('Sim', 'Sim'), ('Lae', 'Lae')], max_length=3, default='Sim', verbose_name="Ativu")
	datetime = models.DateTimeField(null=True)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

	class Meta:
		ordering = ['-ativu', 'nivel', 'pozisaun']

	def unit(self):
		if self.nivel == 'Organizasaun' and self.organizasaun_id and self.municipality_id:
			return f'{self.organizasaun} · {self.municipality}'
		return self.departamentu or self.municipality or self.post or self.village or self.aldeia or self.organizasaun

	def rank(self):
		return POZISAUN_LIST.index(self.pozisaun) if self.pozisaun in POZISAUN_LIST else len(POZISAUN_LIST)

	def __str__(self):
		template = '{0.membro} - {0.pozisaun} {0.nivel}'
		return template.format(self)


class Historia(models.Model):
	"""Log mudansa data (kria, edita, aprova, rejeita, hamoos, aloka)."""
	membro = models.ForeignKey(Membro, on_delete=models.SET_NULL, null=True, blank=True, related_name='historia')
	membro_nome = models.CharField(max_length=150, blank=True)
	aksaun = models.CharField(max_length=30)
	detalhe = models.TextField(blank=True)
	datetime = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

	class Meta:
		ordering = ['-datetime', '-id']

	def __str__(self):
		template = '{0.datetime:%Y-%m-%d %H:%M} {0.aksaun} {0.membro_nome}'
		return template.format(self)
