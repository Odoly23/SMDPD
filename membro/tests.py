import datetime
from django.test import TestCase
from django.urls import reverse
from config import roles
from config.tests import BaseData
from config.user_utils import membro_scope, alokasaun_scope, can_aloka
from membro.models import Membro, Alokasaun


class ScopeTests(BaseData):
	def ids(self, role):
		return set(membro_scope(self.users[role]).values_list('nome', flat=True))

	def test_nasional_hare_hotu(self):
		self.assertEqual(self.ids(roles.PRESIDENTE), {'Joao Silva', 'Maria Costa'})
		self.assertEqual(self.ids(roles.SEKRETARIA), {'Joao Silva', 'Maria Costa'})

	def test_area_hare_deit_nia_rasik(self):
		for role in (roles.KOORD_MUN, roles.KOORD_SUKU, roles.KOORD_ALDEIA, roles.KOORD_ORG):
			self.assertEqual(self.ids(role), {'Joao Silva'}, role)

	def test_departamentu_hare_membru_alokadu(self):
		self.assertEqual(self.ids(roles.KOORD_DEP), set())
		Alokasaun.objects.create(membro=self.m2, nivel='Departamentu', pozisaun='Membru', departamentu=self.dep,
			data_hahu=datetime.date(2026, 1, 1))
		self.assertEqual(self.ids(roles.KOORD_DEP), {'Maria Costa'})
		self.assertEqual(self.ids(roles.PRES_DEP), {'Maria Costa'})

	def test_admin_la_hare_membru(self):
		self.assertEqual(self.ids(roles.ADMIN), set())

	def test_alokasaun_scope_munisipiu(self):
		a1 = Alokasaun.objects.create(membro=self.m1, nivel='Suku', pozisaun='Koordenador', village=self.vil1, data_hahu=datetime.date(2026, 1, 1))
		a2 = Alokasaun.objects.create(membro=self.m2, nivel='Suku', pozisaun='Koordenador', village=self.vil2, data_hahu=datetime.date(2026, 1, 1))
		self.assertEqual(set(alokasaun_scope(self.users[roles.KOORD_MUN])), {a1})
		self.assertEqual(set(alokasaun_scope(self.users[roles.PRESIDENTE])), {a1, a2})

	def test_can_aloka(self):
		self.assertTrue(can_aloka(self.users[roles.PRESIDENTE], 'Suku'))
		self.assertTrue(can_aloka(self.users[roles.PRES_DEP], 'Departamentu', self.dep.pk))
		self.assertFalse(can_aloka(self.users[roles.PRES_DEP], 'Departamentu', self.dep2.pk))
		self.assertFalse(can_aloka(self.users[roles.PRES_DEP], 'Nasional'))
		self.assertFalse(can_aloka(self.users[roles.KOORD_MUN], 'Suku'))


class PermissionTests(BaseData):
	def status(self, role, name, *args):
		self.login(role)
		return self.client.get(reverse(name, args=args)).status_code

	def test_semua_login_redirect(self):
		self.assertEqual(self.client.get(reverse('membro-list')).status_code, 302)

	def test_halaman_utama_hotu_loke(self):
		for role in roles.VIEW_ROLES:
			for name in ('home', 'membro-list', 'report-dash', 'report-chart', 'notif-list'):
				self.assertEqual(self.status(role, name), 200, (role, name))
			for slug in ('nasional', 'departamentu', 'munisipiu', 'suku', 'aldeia', 'organizasaun'):
				self.assertEqual(self.status(role, 'struktura-list', slug), 200, (role, slug))

	def test_admin_halaman(self):
		for name, args in [('home', ()), ('user-list', ()), ('user-add', ()), ('historia-list', ()),
				('master-list', ('munisipiu',)), ('master-list', ('postu',)), ('master-list', ('suku',)),
				('master-list', ('aldeia',)), ('master-list', ('departamentu',)), ('master-list', ('organizasaun',)),
				('master-add', ('suku',)), ('master-add', ('aldeia',))]:
			self.assertEqual(self.status(roles.ADMIN, name, *args), 200, (name, args))

	def test_admin_la_bele_hare_membru(self):
		self.assertEqual(self.status(roles.ADMIN, 'membro-list'), 403)

	def test_non_admin_la_bele_master_user(self):
		for role in roles.VIEW_ROLES:
			self.assertEqual(self.status(role, 'user-list'), 403, role)
			self.assertEqual(self.status(role, 'master-list', 'suku'), 403, role)

	def test_input_deit_ba_peran_input(self):
		for role in roles.VIEW_ROLES:
			esperadu = 200 if role in roles.INPUT_ROLES else 403
			self.assertEqual(self.status(role, 'membro-add'), esperadu, role)

	def test_aprovasaun_deit_presidente(self):
		for role in roles.VIEW_ROLES:
			esperadu = 200 if role in roles.APROVA_ROLES else 403
			self.assertEqual(self.status(role, 'aprovasaun-list'), esperadu, role)

	def test_membru_iha_area_seluk_404(self):
		self.login(roles.KOORD_SUKU)
		self.assertEqual(self.client.get(reverse('membro-detail', args=[self.m2.hashed])).status_code, 404)
		self.assertEqual(self.client.get(reverse('membro-detail', args=[self.m1.hashed])).status_code, 200)

	def test_export_csv(self):
		self.login(roles.KOORD_MUN)
		r = self.client.get(reverse('membro-list') + '?export=csv')
		self.assertEqual(r.status_code, 200)
		body = r.content.decode('utf-8')
		self.assertIn('Joao Silva', body)
		self.assertNotIn('Maria Costa', body)


class MembroFlowTests(BaseData):
	def dados(self, **extra):
		d = {
			'nome': 'Pedro Novo', 'sex': 'Mane', 'date_of_birth': '1995-05-05', 'nu_eleitoral': 'e-9999',
			'municipality': self.mun1.pk, 'post': self.post1.pk, 'village': self.vil1.pk, 'aldeia': self.ald1.pk,
			'status': 'Ativu',
		}
		d.update(extra)
		return d

	def test_sekretaria_input_lalos_ba_pendente_no_notifika_presidente(self):
		self.login(roles.SEKRETARIA)
		r = self.client.post(reverse('membro-add'), self.dados())
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		m = Membro.objects.get(nu_eleitoral='E-9999')
		self.assertEqual(m.aprovasaun, 'Pendente')
		self.assertEqual(m.user, self.users[roles.SEKRETARIA])
		self.assertEqual(self.users[roles.PRESIDENTE].notifikasaun.count(), 1)

	def test_nu_eleitoral_duplikadu_la_bele(self):
		self.login(roles.SEKRETARIA)
		r = self.client.post(reverse('membro-add'), self.dados(nu_eleitoral='e-0001'))
		self.assertEqual(r.status_code, 200)
		self.assertIn('nu_eleitoral', r.context['form'].errors)

	def test_koord_suku_la_bele_input_iha_suku_seluk(self):
		self.login(roles.KOORD_SUKU)
		# aldeia husi suku seluk: rejeita
		r = self.client.post(reverse('membro-add'), self.dados(
			municipality=self.mun2.pk, post=self.post2.pk, village=self.vil2.pk, aldeia=self.ald2.pk))
		self.assertEqual(r.status_code, 200)
		self.assertIn('aldeia', r.context['form'].errors)
		self.assertFalse(Membro.objects.filter(nu_eleitoral='E-9999').exists())
		# aldeia loos, maibé munisipiu/suku manipula: field kunci ho valór husi scope
		r = self.client.post(reverse('membro-add'), self.dados(
			municipality=self.mun2.pk, post=self.post2.pk, village=self.vil2.pk, aldeia=self.ald1.pk))
		self.assertEqual(r.status_code, 302)
		m = Membro.objects.get(nu_eleitoral='E-9999')
		self.assertEqual((m.municipality, m.post, m.village), (self.mun1, self.post1, self.vil1))

	def test_alamat_la_konsistente(self):
		self.login(roles.SEKRETARIA)
		r = self.client.post(reverse('membro-add'), self.dados(aldeia=self.ald2.pk))
		self.assertEqual(r.status_code, 200)
		self.assertIn('aldeia', r.context['form'].errors)

	def test_presidente_aprova_no_rejeita(self):
		m = self.buat('Pendente Um', 'E-5001', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('aprovasaun-aprova', args=[m.hashed]))
		m.refresh_from_db()
		self.assertEqual(m.aprovasaun, 'Aprovadu')
		m2 = self.buat('Pendente Dois', 'E-5002', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.client.post(reverse('aprovasaun-rejeita', args=[m2.hashed]), {'razaun': 'Dadus la kompletu'})
		m2.refresh_from_db()
		self.assertEqual(m2.aprovasaun, 'Rejeitadu')

	def test_sekretaria_la_bele_aprova(self):
		m = self.buat('Pendente Um', 'E-5001', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.login(roles.SEKRETARIA)
		r = self.client.post(reverse('aprovasaun-aprova', args=[m.hashed]))
		self.assertEqual(r.status_code, 403)

	def test_edita_fila_ba_pendente(self):
		self.login(roles.KOORD_SUKU)
		r = self.client.post(reverse('membro-update', args=[self.m1.hashed]), self.dados(nome='Joao Silva Editadu', nu_eleitoral='E-0001'))
		self.assertEqual(r.status_code, 302)
		self.m1.refresh_from_db()
		self.assertEqual(self.m1.aprovasaun, 'Pendente')
		self.assertEqual(self.m1.nome, 'Joao Silva Editadu')


class AlokasaunTests(BaseData):
	def dados(self, membro, nivel, pozisaun, **extra):
		d = {'membro': membro.pk, 'nivel': nivel, 'pozisaun': pozisaun, 'data_hahu': '2026-01-01', 'ativu': 'Sim'}
		d.update(extra)
		return d

	def test_presidente_nasional(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Nasional', 'Presidente'))
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		self.assertTrue(Alokasaun.objects.filter(nivel='Nasional', pozisaun='Presidente', membro=self.m1).exists())

	def test_pozisaun_unik_iha_unidade(self):
		self.login(roles.SEKRETARIA)
		self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Nasional', 'Vice 1'))
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m2, 'Nasional', 'Vice 1'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual(Alokasaun.objects.filter(nivel='Nasional', pozisaun='Vice 1').count(), 1)

	def test_membru_bele_barak(self):
		self.login(roles.PRESIDENTE)
		self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Nasional', 'Membru'))
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m2, 'Nasional', 'Membru'))
		self.assertEqual(r.status_code, 302)
		self.assertEqual(Alokasaun.objects.filter(nivel='Nasional', pozisaun='Membru').count(), 2)

	def test_pozisaun_la_existe_iha_nivel(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Organizasaun', 'Vice 1', organizasaun=self.org.pk))
		self.assertEqual(r.status_code, 200)
		self.assertIn('pozisaun', r.context['form'].errors)

	def test_departamentu_pozisaun(self):
		self.login(roles.PRESIDENTE)
		for poz in ('Presidente Departamentu', 'Koordenador', 'Vice 1', 'Vice 4', 'Membru'):
			r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', poz, departamentu=self.dep.pk))
			self.assertEqual(r.status_code, 302, (poz, getattr(r, 'context', None) and r.context['form'].errors))

	def test_presidente_departamentu_deit_nia_departamentu(self):
		self.login(roles.PRES_DEP)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', 'Koordenador', departamentu=self.dep.pk))
		self.assertEqual(r.status_code, 302)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Departamentu', 'Koordenador', departamentu=self.dep2.pk))
		self.assertEqual(r.status_code, 200)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Nasional', 'Presidente'))
		self.assertEqual(r.status_code, 200)
		self.assertFalse(Alokasaun.objects.filter(nivel='Nasional').exists())

	def test_presidente_departamentu_la_bele_edita_departamentu_seluk(self):
		a = Alokasaun.objects.create(membro=self.m1, nivel='Departamentu', pozisaun='Membru', departamentu=self.dep2, data_hahu=datetime.date(2026, 1, 1))
		self.login(roles.PRES_DEP)
		self.assertEqual(self.client.get(reverse('alokasaun-update', args=[a.pk])).status_code, 403)
		self.assertEqual(self.client.post(reverse('alokasaun-del', args=[a.pk])).status_code, 403)
		self.assertTrue(Alokasaun.objects.filter(pk=a.pk).exists())

	def test_koord_mun_la_bele_aloka(self):
		self.login(roles.KOORD_MUN)
		self.assertEqual(self.client.get(reverse('alokasaun-add')).status_code, 403)

	def test_membru_tenke_hela_iha_suku(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m2, 'Suku', 'Koordenador',
			municipality=self.mun1.pk, post=self.post1.pk, village=self.vil1.pk))
		self.assertEqual(r.status_code, 200)
		self.assertIn('membro', r.context['form'].errors)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Suku', 'Koordenador',
			municipality=self.mun1.pk, post=self.post1.pk, village=self.vil1.pk))
		self.assertEqual(r.status_code, 302)

	def test_aldeia_no_edita(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(self.m1, 'Aldeia', 'Sekretaria',
			municipality=self.mun1.pk, post=self.post1.pk, village=self.vil1.pk, aldeia=self.ald1.pk))
		self.assertEqual(r.status_code, 302)
		a = Alokasaun.objects.get(nivel='Aldeia')
		self.assertIsNone(a.village_id)
		self.assertEqual(self.client.get(reverse('alokasaun-update', args=[a.pk])).status_code, 200)

	def test_membru_pendente_la_bele_hetan_pozisaun(self):
		p = self.buat('Pendente', 'E-7000', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('alokasaun-add'), self.dados(p, 'Nasional', 'Membru'))
		self.assertEqual(r.status_code, 200)
		self.assertIn('membro', r.context['form'].errors)

	def test_search_membru(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-search'), {'q': 'joao'})
		self.assertContains(r, 'Joao Silva')
		self.assertNotContains(r, 'Maria')


class AjaxTests(BaseData):
	def test_chain(self):
		self.login(roles.SEKRETARIA)
		self.assertContains(self.client.get(reverse('ajax_load_posts'), {'municipality': self.mun1.pk}), 'Dom Aleixo')
		self.assertContains(self.client.get(reverse('ajax_load_villages'), {'post': self.post1.pk}), 'Comoro')
		self.assertContains(self.client.get(reverse('ajax_load_aldeias'), {'village': self.vil1.pk}), 'Aldeia A')
		self.assertNotContains(self.client.get(reverse('ajax_load_aldeias'), {'village': self.vil1.pk}), 'Aldeia B')


class ReportTests(BaseData):
	def test_api_hanesan_scope(self):
		self.login(roles.KOORD_MUN)
		d = self.client.get(reverse('api-gender')).json()
		self.assertEqual(d['obj'], [1])
		self.login(roles.PRESIDENTE)
		d = self.client.get(reverse('api-gender')).json()
		self.assertEqual(sum(d['obj']), 2)
		for name in ('api-age', 'api-hakbit', 'api-munisipiu', 'api-organizasaun', 'api-marital', 'api-status', 'api-aprovasaun', 'api-postu', 'api-suku', 'api-aldeia'):
			self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

	def test_api_admin_proibidu(self):
		self.login(roles.ADMIN)
		self.assertEqual(self.client.get(reverse('api-gender')).status_code, 403)

	def test_relatoriu_departamentu_la_duplika(self):
		for poz in ('Membru', 'Koordenador'):
			Alokasaun.objects.create(membro=self.m1, nivel='Departamentu', pozisaun=poz, departamentu=self.dep, data_hahu=datetime.date(2026, 1, 1))
		self.login(roles.KOORD_DEP)
		self.assertEqual(self.client.get(reverse('report-dash')).context['tot']['total'], 1)
		d = self.client.get(reverse('api-gender')).json()
		self.assertEqual(d['obj'], [1])
