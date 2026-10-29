from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from config import roles
from config.tests import BaseData
from user.models import UserScope


class KeamananTests(BaseData):
	def setUp(self):
		cache.clear()

	def test_password_foun_obriga_troka(self):
		u = self.users[roles.SEKRETARIA]
		UserScope.objects.filter(user=u).update(troka_password=True)
		self.client.force_login(u)
		for url in (reverse('home'), reverse('membro-list'), '/admin/'):
			self.assertRedirects(self.client.get(url), reverse('change-password'), fetch_redirect_response=False)
		self.assertEqual(self.client.get(reverse('change-password')).status_code, 200)   # pájina troka password livre
		self.assertContains(self.client.get(reverse('change-password')), 'password mak foun')
		self.assertEqual(self.client.post(reverse('logout')).status_code, 302)           # bele sai

	def test_troka_password_hamoos_obrigasaun(self):
		u = self.users[roles.SEKRETARIA]
		UserScope.objects.filter(user=u).update(troka_password=True)
		self.client.force_login(u)
		r = self.client.post(reverse('change-password'), {'old_password': 'x-Senha-123', 'new_password1': 'Troka-Foun-5555', 'new_password2': 'Troka-Foun-5555'})
		self.assertEqual(r.status_code, 302)
		self.assertFalse(UserScope.objects.get(user=u).troka_password)
		self.assertEqual(self.client.get(reverse('home')).status_code, 200)

	def test_password_sala_la_hamoos_obrigasaun(self):
		u = self.users[roles.SEKRETARIA]
		UserScope.objects.filter(user=u).update(troka_password=True)
		self.client.force_login(u)
		r = self.client.post(reverse('change-password'), {'old_password': 'sala', 'new_password1': 'Troka-Foun-5555', 'new_password2': 'Troka-Foun-5555'})
		self.assertEqual(r.status_code, 200)
		self.assertTrue(UserScope.objects.get(user=u).troka_password)

	def test_admin_kria_uzuariu_hetan_obrigasaun(self):
		self.client.force_login(self.users[roles.ADMIN])
		self.client.post(reverse('user-add'), {'username': 'baru', 'first_name': 'Baru', 'is_active': 'on', 'group': roles.PRESIDENTE, 'password': 'Senha-Forte-987'})
		self.assertTrue(UserScope.objects.get(user__username='baru').troka_password)

	def test_la_iha_obrigasaun_normal(self):
		self.client.force_login(self.users[roles.SEKRETARIA])
		self.assertEqual(self.client.get(reverse('home')).status_code, 200)

	def test_lokdaun_tentativa_sala(self):
		dados = {'username': roles.PRESIDENTE, 'password': 'sala'}
		for _ in range(5):
			r = self.client.post(reverse('login'), dados)
			self.assertEqual(r.status_code, 200)
		r = self.client.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': 'x-Senha-123'})   # password loos mós blokeia
		self.assertEqual(r.status_code, 429)
		self.assertContains(r, 'Tentativa sala barak liu', status_code=429)

	def test_lokdaun_la_afeta_uzuariu_seluk(self):
		for _ in range(5):
			self.client.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': 'sala'})
		r = self.client.post(reverse('login'), {'username': roles.SEKRETARIA, 'password': 'x-Senha-123'})
		self.assertEqual(r.status_code, 302)

	def test_login_susesu_hamoos_kontador(self):
		for _ in range(3):
			self.client.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': 'sala'})
		self.assertEqual(self.client.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': 'x-Senha-123'}).status_code, 302)
		self.client.post(reverse('logout'))
		for _ in range(4):
			self.assertEqual(self.client.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': 'sala'}).status_code, 200)
