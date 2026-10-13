import datetime
from django.contrib.auth.models import Group, User
from django.test import TestCase
from config import roles
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun
from membro.models import Membro, Alokasaun
from user.models import UserScope


class BaseData(TestCase):
	"""Data dasar: 2 munisipiu, suku/aldeia, departamentu, organizasaun no user ba peran hotu."""

	@classmethod
	def setUpTestData(cls):
		for key, _ in roles.ROLE_LABELS:
			Group.objects.get_or_create(name=key)
		cls.mun1 = Municipality.objects.create(name='Dili', code='DI')
		cls.mun2 = Municipality.objects.create(name='Baucau', code='BC')
		cls.post1 = AdministrativePost.objects.create(municipality=cls.mun1, name='Dom Aleixo')
		cls.post2 = AdministrativePost.objects.create(municipality=cls.mun2, name='Baucau Vila')
		cls.vil1 = Village.objects.create(administrativepost=cls.post1, name='Comoro')
		cls.vil2 = Village.objects.create(administrativepost=cls.post2, name='Bahu')
		cls.ald1 = Aldeia.objects.create(village=cls.vil1, name='Aldeia A')
		cls.ald2 = Aldeia.objects.create(village=cls.vil2, name='Aldeia B')
		cls.dep = Departamentu.objects.create(code='FIN', name='Finansas')
		cls.dep2 = Departamentu.objects.create(code='INF', name='Informasaun')
		cls.org = Organizasaun.objects.create(code='OJP', name='Organizasaun Juventude')
		cls.users = {}
		scopes = {
			roles.ADMIN: {}, roles.PRESIDENTE: {}, roles.SEKRETARIA: {},
			roles.PRES_DEP: {'departamentu': cls.dep}, roles.KOORD_DEP: {'departamentu': cls.dep},
			roles.KOORD_MUN: {'municipality': cls.mun1}, roles.KOORD_SUKU: {'village': cls.vil1},
			roles.KOORD_ALDEIA: {'aldeia': cls.ald1}, roles.KOORD_ORG: {'organizasaun': cls.org},
		}
		for role, scope in scopes.items():
			u = User.objects.create_user(role, password='x-Senha-123', first_name=role)
			u.groups.add(Group.objects.get(name=role))
			UserScope.objects.create(user=u, **scope)
			cls.users[role] = u
		cls.m1 = cls.buat('Joao Silva', 'E-0001', cls.mun1, cls.post1, cls.vil1, cls.ald1, org=cls.org)
		cls.m2 = cls.buat('Maria Costa', 'E-0002', cls.mun2, cls.post2, cls.vil2, cls.ald2)

	@staticmethod
	def buat(nome, eleitoral, mun, post, vil, ald, org=None, aprovasaun='Aprovadu', sex='Mane'):
		return Membro.objects.create(
			nome=nome, sex=sex, date_of_birth=datetime.date(1990, 1, 1), nu_eleitoral=eleitoral,
			municipality=mun, post=post, village=vil, aldeia=ald, organizasaun=org, aprovasaun=aprovasaun)

	def login(self, role):
		self.client.force_login(self.users[role])
