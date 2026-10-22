from django.contrib.auth.models import User
from django.urls import reverse
from config import roles
from config.tests import BaseData


class UserTests(BaseData):
	def dados(self, **extra):
		d = {'username': 'baru', 'first_name': 'Baru', 'email': '', 'is_active': 'on', 'group': roles.KOORD_SUKU,
			'password': 'Senha-Forte-987', 'village': self.vil1.pk}
		d.update(extra)
		return d

	def test_admin_kria_koord_suku(self):
		self.login(roles.ADMIN)
		r = self.client.post(reverse('user-add'), self.dados())
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		u = User.objects.get(username='baru')
		self.assertEqual(u.groups.first().name, roles.KOORD_SUKU)
		self.assertEqual(u.scope.village, self.vil1)

	def test_peran_area_tenke_hili(self):
		self.login(roles.ADMIN)
		for role, keep in [(roles.KOORD_SUKU, 'village'), (roles.KOORD_MUN, 'municipality'), (roles.KOORD_POSTU, 'post'), (roles.KOORD_ALDEIA, 'aldeia'),
				(roles.KOORD_ORG, 'organizasaun'), (roles.PRES_DEP, 'departamentu'), (roles.KOORD_DEP, 'departamentu')]:
			r = self.client.post(reverse('user-add'), self.dados(group=role, village='', username=f'x{role}'))
			self.assertEqual(r.status_code, 200, role)
			self.assertIn(keep, r.context['form'].errors, role)

	def test_peran_nasional_la_presiza_area(self):
		self.login(roles.ADMIN)
		r = self.client.post(reverse('user-add'), self.dados(group=roles.PRESIDENTE, username='pres2'))
		self.assertEqual(r.status_code, 302)
		self.assertIsNone(User.objects.get(username='pres2').scope.village)

	def test_la_bele_desativa_an_rasik(self):
		self.login(roles.ADMIN)
		u = self.users[roles.ADMIN]
		r = self.client.post(reverse('user-update', args=[u.pk]), {'username': u.username, 'first_name': 'A', 'email': '',
			'group': roles.ADMIN, 'password': ''})
		self.assertEqual(r.status_code, 200)
		u.refresh_from_db()
		self.assertTrue(u.is_active)


import io
import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from custom.models import Organizasaun


def gambar(nome='logo.png'):
	buf = io.BytesIO()
	Image.new('RGB', (40, 40), (200, 30, 30)).save(buf, 'PNG')
	return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/png')


class LogoNavbarTests(BaseData):
	@classmethod
	def setUpClass(cls):
		cls._media = tempfile.mkdtemp()
		cls._override = override_settings(MEDIA_ROOT=cls._media)
		cls._override.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._override.disable()
		shutil.rmtree(cls._media, ignore_errors=True)

	def test_orgaun_ho_logo_hatudu_logo_rasik(self):
		self.org.logo = gambar()
		self.org.save()
		self.login(roles.KOORD_ORG)
		r = self.client.get(reverse('home'))
		self.assertContains(r, self.org.logo.url)
		self.assertContains(r, self.org.name)
		self.assertNotContains(r, 'logo_plp.png"')  # la hatudu logo PLP iha navbar

	def test_orgaun_sein_logo_fila_ba_plp(self):
		self.login(roles.KOORD_ORG)
		r = self.client.get(reverse('home'))
		self.assertContains(r, 'logo_plp.png')

	def test_struktura_nasionál_hatudu_logo_plp(self):
		self.org.logo = gambar()
		self.org.save()
		for role in (roles.PRESIDENTE, roles.SEKRETARIA, roles.KOORD_MUN, roles.KOORD_DEP, roles.ADMIN):
			self.login(role)
			r = self.client.get(reverse('home'))
			self.assertContains(r, 'logo_plp.png', msg_prefix=role)
			self.assertNotContains(r, self.org.logo.url, msg_prefix=role)

	def test_admin_upload_logo_orgaun(self):
		self.login(roles.ADMIN)
		r = self.client.post(reverse('master-update', args=['organizasaun', self.org.pk]),
			{'code': self.org.code, 'name': self.org.name, 'is_active': 'on', 'logo': gambar()})
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		self.org.refresh_from_db()
		self.assertTrue(self.org.logo.name.startswith('logo_orgaun/'))
