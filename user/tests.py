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
		for role, keep in [(roles.KOORD_SUKU, 'village'), (roles.KOORD_MUN, 'municipality'), (roles.KOORD_ALDEIA, 'aldeia'),
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
