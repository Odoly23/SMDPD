import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from config import roles
from config.tests import BaseData
from config.user_utils import alokasaun_scope, can_aloka
from membro.akun import sinkroniza_login
from membro.models import Alokasaun
from user.models import UserScope


class OrgStrukturaTests(BaseData):
	def aloka(self, membro, nivel, pozisaun, **kw):
		return Alokasaun.objects.create(membro=membro, nivel=nivel, pozisaun=pozisaun, data_hahu=datetime.date(2026, 1, 1), **kw)

	def dados(self, membro, nivel, pozisaun, **extra):
		d = {'membro': membro.pk, 'nivel': nivel, 'pozisaun': pozisaun, 'data_hahu': '2026-01-01', 'ativu': 'Sim'}
		d.update(extra)
		return d

	def test_orgaun_iha_pozisaun_presidente_vice_sekretaria(self):
		self.login(roles.PRESIDENTE)
		for poz in ('Presidente', 'Vice 1', 'Vice 2', 'Vice 3', 'Vice 4', 'Sekretaria', 'Koordenador'):
			r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Organizasaun', poz, organizasaun=self.org.pk))
			self.assertEqual(r.status_code, 302, (poz, getattr(r, 'context', None) and r.context['form'].errors))

	def test_departamentu_iha_orgaun(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', 'Koordenador', departamentu=self.dep_org.pk))
		self.assertEqual(r.status_code, 302)  # m1 tama orgaun
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m2, 'Departamentu', 'Koordenador', departamentu=self.dep_org.pk))
		self.assertEqual(r.status_code, 200)  # m2 la tama orgaun
		self.assertIn('membro', r.context['form'].errors)
		self.assertEqual(str(self.dep_org), 'Finansas (OJP)')

	def test_presidente_orgaun_aloka_deit_iha_orgaun_rasik(self):
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.get(reverse('alokasaun-add')).status_code, 200)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org.pk))
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', 'Membru', departamentu=self.dep_org.pk))
		self.assertEqual(r.status_code, 302)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Organizasaun', 'Koordenador', organizasaun=self.org2.pk))
		self.assertEqual(r.status_code, 200)       # orgaun seluk
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Nasional', 'Presidente'))
		self.assertEqual(r.status_code, 200)       # nivel la bele
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', 'Membru', departamentu=self.dep.pk))
		self.assertEqual(r.status_code, 200)       # departamentu nasionál
		self.assertFalse(Alokasaun.objects.filter(nivel='Nasional').exists())

	def test_peran_orgaun_seluk_la_bele_aloka(self):
		for role in (roles.VICE_ORG, roles.SEKR_ORG, roles.KOORD_ORG):
			self.login(role)
			self.assertEqual(self.client.get(reverse('alokasaun-add')).status_code, 403, role)

	def test_can_aloka_orgaun(self):
		u = self.users[roles.PRES_ORG]
		self.assertTrue(can_aloka(u, 'Organizasaun', organizasaun_id=self.org.pk))
		self.assertFalse(can_aloka(u, 'Organizasaun', organizasaun_id=self.org2.pk))
		self.assertTrue(can_aloka(u, 'Departamentu', departamentu_id=self.dep_org.pk))
		self.assertFalse(can_aloka(u, 'Departamentu', departamentu_id=self.dep.pk))

	def test_alokasaun_scope_orgaun(self):
		a1 = self.aloka(self.m1, 'Organizasaun', 'Presidente', organizasaun=self.org)
		a2 = self.aloka(self.m1, 'Departamentu', 'Membru', departamentu=self.dep_org)
		self.aloka(self.m2, 'Departamentu', 'Membru', departamentu=self.dep)
		self.assertEqual(set(alokasaun_scope(self.users[roles.PRES_ORG])), {a1, a2})

	def test_presidente_orgaun_la_bele_edita_orgaun_seluk(self):
		a = self.aloka(self.m2, 'Organizasaun', 'Koordenador', organizasaun=self.org2)
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.get(reverse('alokasaun-update', args=[a.pk])).status_code, 403)
		self.assertEqual(self.client.post(reverse('alokasaun-del', args=[a.pk])).status_code, 403)

	def test_sekretaria_orgaun_input_anggota_orgaun_deit(self):
		self.login(roles.SEKR_ORG)
		self.assertEqual(self.client.get(reverse('membro-add')).status_code, 200)
		self.login(roles.VICE_ORG)
		self.assertEqual(self.client.get(reverse('membro-add')).status_code, 403)
		self.assertEqual(self.client.get(reverse('membro-list')).status_code, 200)

	def test_menu_struktura_tuir_peran(self):
		self.login(roles.PRES_ORG)
		r = self.client.get(reverse('home'))
		slugs = [c['url'] for it in r.context['nav_items'] for c in it['children']]
		self.assertTrue(any('organizasaun' in u for u in slugs))
		self.assertFalse(any('/suku/' in u for u in slugs))

	def test_logo_departamentu_orgaun(self):
		self.org.name = 'Sentru Estudu Estratejiku'
		self.org.save()
		u = User.objects.get(username=roles.KOORD_DEP)
		s = u.scope
		s.departamentu = self.dep_org
		s.save()
		self.login(roles.KOORD_DEP)
		self.assertContains(self.client.get(reverse('home')), 'Sentru Estudu Estratejiku')


class LoginAkunTests(BaseData):
	def aloka(self, membro, nivel, pozisaun, **kw):
		return Alokasaun.objects.create(membro=membro, nivel=nivel, pozisaun=pozisaun, data_hahu=datetime.date(2026, 1, 1), **kw)

	def test_presidente_orgaun_kria_login_sekretaria(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRES_ORG)
		r = self.client.post(reverse('login-kria', args=[a.pk]))
		self.assertEqual(r.status_code, 200)
		u = User.objects.get(scope__membro=self.m1)
		self.assertTrue(r.context['password'])
		self.assertTrue(u.check_password(r.context['password']))
		self.assertEqual(u.groups.first().name, roles.SEKR_ORG)
		self.assertEqual(u.scope.organizasaun, self.org)
		self.assertEqual(u.username, 'e0001')
		# akun bele login no hatudu navbar orgaun
		self.client.logout()
		self.assertTrue(self.client.login(username='e0001', password=r.context['password']))
		# password foun: tenke troka uluk
		self.assertRedirects(self.client.get(reverse('membro-add')), reverse('change-password'))
		r2 = self.client.post(reverse('change-password'), {'old_password': r.context['password'], 'new_password1': 'Senha-Foun-9876', 'new_password2': 'Senha-Foun-9876'})
		self.assertEqual(r2.status_code, 302)
		self.assertEqual(self.client.get(reverse('membro-add')).status_code, 200)

	def test_presidente_orgaun_la_bele_kria_login_presidente_orgaun(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Presidente', organizasaun=self.org)
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 403)
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 200)

	def test_sekretaria_nasionál_la_bele_kria_login_nasionál(self):
		a = self.aloka(self.m1, 'Nasional', 'Presidente')
		self.login(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 403)
		self.assertFalse(UserScope.objects.filter(membro=self.m1).exists())
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 200)

	def test_membru_ordinariu_la_iha_login(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Membru', organizasaun=self.org)
		for role in (roles.PRESIDENTE, roles.PRES_ORG):
			self.login(role)
			self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 403, role)
		b = self.aloka(self.m1, 'Aldeia', 'Sekretaria', aldeia=self.ald1)   # pozisaun la bele login
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('login-kria', args=[b.pk])).status_code, 403)

	def test_presidente_departamentu_kria_login_koordenador_deit(self):
		a = self.aloka(self.m1, 'Departamentu', 'Koordenador', departamentu=self.dep)
		p = self.aloka(self.m2, 'Departamentu', 'Presidente Departamentu', departamentu=self.dep)
		self.login(roles.PRES_DEP)
		self.assertEqual(self.client.post(reverse('login-kria', args=[a.pk])).status_code, 200)
		self.assertEqual(self.client.post(reverse('login-kria', args=[p.pk])).status_code, 403)

	def test_membru_pendente_la_hetan_login(self):
		pend = self.buat('Pendente', 'E-8001', self.mun1, self.post1, self.vil1, self.ald1, org=self.org, aprovasaun='Pendente')
		a = self.aloka(pend, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('login-kria', args=[a.pk]))
		self.assertEqual(r.status_code, 302)
		self.assertFalse(UserScope.objects.filter(membro=pend).exists())

	def test_reset_password_la_duplika_akun(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Vice 1', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		p1 = self.client.post(reverse('login-kria', args=[a.pk])).context['password']
		p2 = self.client.post(reverse('login-kria', args=[a.pk])).context['password']
		self.assertNotEqual(p1, p2)
		self.assertEqual(User.objects.filter(scope__membro=self.m1).count(), 1)
		self.assertTrue(User.objects.get(scope__membro=self.m1).check_password(p2))

	def test_sinkroniza_bainhira_pozisaun_troka(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('login-kria', args=[a.pk]))
		u = User.objects.get(scope__membro=self.m1)
		# pozisaun hamoos -> konta desativa
		self.client.post(reverse('alokasaun-del', args=[a.pk]))
		u.refresh_from_db()
		self.assertFalse(u.is_active)
		# pozisaun foun (Presidente orgaun) -> konta ativu fali ho peran foun
		self.client.post(reverse('alokasaun-add'), {'membro': self.m1.pk, 'nivel': 'Organizasaun', 'pozisaun': 'Presidente',
			'organizasaun': self.org.pk, 'data_hahu': '2026-02-01', 'ativu': 'Sim'})
		u.refresh_from_db()
		self.assertTrue(u.is_active)
		self.assertEqual(u.groups.first().name, roles.PRES_ORG)

	def test_prioridade_peran(self):
		self.aloka(self.m1, 'Organizasaun', 'Vice 1', organizasaun=self.org)
		a = self.aloka(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('login-kria', args=[a.pk]))
		self.assertEqual(User.objects.get(scope__membro=self.m1).groups.first().name, roles.SEKR_ORG)

	def test_membru_inativu_desativa_login(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('login-kria', args=[a.pk]))
		self.m1.status = 'Falesidu'
		self.m1.save()
		u = sinkroniza_login(self.m1)
		self.assertFalse(u.is_active)

	def test_hamoos_membru_desativa_login(self):
		a = self.aloka(self.m1, 'Organizasaun', 'Sekretaria', organizasaun=self.org)
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('login-kria', args=[a.pk]))
		u = User.objects.get(scope__membro=self.m1)
		self.client.post(reverse('membro-del', args=[self.m1.hashed]))
		u.refresh_from_db()
		self.assertFalse(u.is_active)
