import datetime
from django.urls import reverse
from django.utils import timezone
from config import roles
from config.tests import BaseData
from membro.models import Alokasaun

HOJE = datetime.date(2024, 1, 1)


class PainelTests(BaseData):
	@classmethod
	def setUpTestData(cls):
		super().setUpTestData()
		cls.m3 = cls.buat('Ana Feto', 'E-0003', cls.mun1, cls.post1, cls.vil1, cls.ald1, sex='Feto')
		cls.m3.data_hakbit = datetime.date(timezone.now().year, 2, 1)
		cls.m3.save()
		Alokasaun.objects.create(membro=cls.m1, nivel='Departamentu', pozisaun='Presidente Departamentu', departamentu=cls.dep, ativu='Sim', data_hahu=HOJE)
		Alokasaun.objects.create(membro=cls.m1, nivel='Nasional', pozisaun='Presidente', ativu='Sim', data_hahu=HOJE)
		Alokasaun.objects.create(membro=cls.m2, nivel='Organizasaun', pozisaun='Presidente', organizasaun=cls.org, ativu='Sim', data_hahu=HOJE)
		Alokasaun.objects.create(membro=cls.m3, nivel='Departamentu', pozisaun='Membru', departamentu=cls.dep_org, ativu='Sim', data_hahu=HOJE)

	def home(self, role, **params):
		self.login(role)
		r = self.client.get(reverse('home'), params)
		self.assertEqual(r.status_code, 200)
		return r

	def test_presidente_hare_entidade_hotu(self):
		r = self.home(roles.PRESIDENTE)
		self.assertEqual([e['naran'] for e in r.context['entidades']], ['PLP Nasionál', 'Organizasaun Feto', 'Organizasaun Juventude'])
		self.assertEqual(r.context['entidades'][0]['total'], 3)
		self.assertEqual(r.context['entidades'][0]['lider'], 'Joao Silva')
		self.assertEqual(r.context['titulu_area'], 'Munisipiu')
		self.assertContains(r, 'Liafuan xave')
		self.assertNotContains(r, 'Asuntu')

	def test_grafik_mane_feto_tuir_munisipiu(self):
		r = self.home(roles.PRESIDENTE)
		c = r.context
		d = dict(zip(c['grafik_label'], zip(c['grafik_mane'], c['grafik_feto'])))
		self.assertEqual(d['Dili'], (1, 1))
		self.assertEqual(d['Baucau'], (1, 0))
		self.assertEqual(c['tinan'], timezone.now().year)

	def test_grafik_foun_deit_tinan_ne(self):
		r = self.home(roles.PRESIDENTE, mode='foun')
		c = r.context
		self.assertEqual((sum(c['grafik_mane']), sum(c['grafik_feto'])), (0, 1))
		r = self.home(roles.PRESIDENTE, mode='foun', tinan=timezone.now().year - 1)
		self.assertEqual((sum(r.context['grafik_mane']), sum(r.context['grafik_feto'])), (0, 0))

	def test_tinan_la_validu_uza_tinan_ohin(self):
		r = self.home(roles.PRESIDENTE, tinan='abc')
		self.assertEqual(r.context['tinan'], timezone.now().year)
		r = self.home(roles.PRESIDENTE, tinan='1')
		self.assertEqual(r.context['tinan'], timezone.now().year)

	def test_grafik_inativu_la_konta(self):
		self.m2.status = 'Inativu'
		self.m2.save()
		c = self.home(roles.PRESIDENTE).context
		self.assertEqual(dict(zip(c['grafik_label'], c['grafik_mane']))['Baucau'], 0)

	def test_membru_laiha_area_hatudu_nota(self):
		self.m1.municipality = None
		self.m1.save()
		r = self.home(roles.PRESIDENTE)
		self.assertEqual(r.context['sen_area'], 1)
		self.assertContains(r, 'seidauk iha munisipiu')

	def test_koord_munisipiu_hare_postu_rasik(self):
		r = self.home(roles.KOORD_MUN)
		self.assertContains(r, 'DOM ALEIXO')
		self.assertNotContains(r, 'BAUCAU VILA')
		self.assertEqual(r.context['grafik_label'], ['Dom Aleixo'])
		self.assertEqual(r.context['counts']['total'], 2)

	def test_koord_postu_no_suku(self):
		r = self.home(roles.KOORD_POSTU)
		self.assertContains(r, 'COMORO')
		self.assertNotContains(r, 'BAHU')
		self.assertEqual(self.home(roles.KOORD_SUKU).context['grafik_label'], ['Aldeia A'])

	def test_koord_aldeia_grafik_ida(self):
		c = self.home(roles.KOORD_ALDEIA).context
		self.assertEqual(c['grafik_label'], ['Aldeia A'])
		self.assertEqual((c['grafik_mane'], c['grafik_feto']), ([1], [1]))

	def test_pres_departamentu_deit_nia_entidade(self):
		r = self.home(roles.PRES_DEP)           # dep nasionál (la iha orgaun)
		self.assertEqual([e['naran'] for e in r.context['entidades']], ['PLP Nasionál'])

	def test_orgaun_deit_nia_orgaun(self):
		r = self.home(roles.PRES_ORG)
		self.assertEqual([e['naran'] for e in r.context['entidades']], ['Organizasaun Juventude'])
		self.assertNotContains(r, 'Organizasaun Feto')

	def test_admin_la_iha_painel(self):
		self.login(roles.ADMIN)
		self.assertNotIn('entidades', self.client.get(reverse('home')).context)

	# ---- detallu entidade ----
	def test_entidade_nasional(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('entidade-nasional'))
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, 'Joao Silva')
		self.assertEqual([x['dep'].name for x in r.context['rows']], ['Finansas', 'Informasaun'])
		self.assertEqual(r.context['rows'][0]['presidente'], 'Joao Silva')
		self.assertEqual(r.context['rows'][0]['total'], 1)

	def test_entidade_orgaun_lideransa_no_departamentu(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('entidade-orgaun', args=[self.org.hashed]))
		self.assertEqual(r.status_code, 200)
		self.assertEqual([a.membro.nome for a in r.context['lideransa']], ['Maria Costa'])
		self.assertEqual([x['dep'].pk for x in r.context['rows']], [self.dep_org.pk])
		self.assertEqual(r.context['rows'][0]['total'], 1)
		self.assertEqual(r.context['total'], 1)       # membru ho organizasaun=org deit (m1)

	def test_entidade_orgaun_seluk_404_ba_orgaun(self):
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.get(reverse('entidade-orgaun', args=[self.org.hashed])).status_code, 200)
		self.assertEqual(self.client.get(reverse('entidade-orgaun', args=[self.org2.hashed])).status_code, 404)
		self.assertEqual(self.client.get(reverse('entidade-nasional')).status_code, 404)

	def test_entidade_departamentu_deit_nia_tabela(self):
		self.login(roles.PRES_DEP)
		r = self.client.get(reverse('entidade-nasional'))
		self.assertEqual([x['dep'].name for x in r.context['rows']], ['Finansas'])
		self.assertEqual(self.client.get(reverse('entidade-orgaun', args=[self.org.hashed])).status_code, 404)

	def test_entidade_koord_suku_total_iha_área(self):
		self.login(roles.KOORD_SUKU)
		r = self.client.get(reverse('entidade-nasional'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r.context['total'], 2)   # m1 + m3 iha suku ne'e; m2 la
		self.assertNotContains(r, 'Maria Costa')

	def test_entidade_admin_no_anonimu(self):
		self.login(roles.ADMIN)
		self.assertEqual(self.client.get(reverse('entidade-nasional')).status_code, 404)
		self.client.logout()
		self.assertEqual(self.client.get(reverse('entidade-nasional')).status_code, 302)

	def test_filtru_departamentu_iha_lista(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-list') + '?departamentu=%d' % self.dep.pk)
		self.assertContains(r, 'Joao Silva')
		self.assertNotContains(r, 'Maria Costa')


class KartaunHotuTests(BaseData):
	def get(self, role, **params):
		self.login(role)
		return self.client.get(reverse('membro-kartaun-hotu'), params)

	def test_hotu_aprovadu_deit(self):
		self.buat('Pendente Sa', 'E-9100', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		r = self.get(roles.PRESIDENTE)
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r.context['total'], 2)
		self.assertContains(r, 'Joao Silva')
		self.assertContains(r, 'Maria Costa')
		self.assertNotContains(r, 'Pendente Sa')

	def test_tuir_peran_no_filtru(self):
		r = self.get(roles.KOORD_SUKU)
		self.assertContains(r, 'Joao Silva')
		self.assertNotContains(r, 'Maria Costa')
		r = self.get(roles.PRESIDENTE, organizasaun=self.org.pk)
		self.assertEqual(r.context['total'], 1)

	def test_folha_10_kartaun(self):
		for i in range(12):
			self.buat('Membru %d' % i, 'E-5%03d' % i, self.mun1, self.post1, self.vil1, self.ald1)
		r = self.get(roles.PRESIDENTE)
		self.assertEqual([len(f) for f in r.context['folhas']], [10, 4])

	def test_cetak_depan_no_kotuk(self):
		r = self.get(roles.PRESIDENTE, cetak=1)
		self.assertTemplateUsed(r, 'membro/kartaun_hotu_print.html')
		self.assertContains(r, 'kartaun-frente')
		r = self.get(roles.PRESIDENTE, cetak=1, sisi='kotuk')
		self.assertContains(r, 'kartaun-kotuk')
		self.assertNotContains(r, 'kartaun-frente')

	def test_admin_la_bele_no_anonimu(self):
		self.assertEqual(self.get(roles.ADMIN).status_code, 403)
		self.client.logout()
		self.assertEqual(self.client.get(reverse('membro-kartaun-hotu')).status_code, 302)

	def test_botaun_iha_lista(self):
		self.login(roles.PRESIDENTE)
		self.assertContains(self.client.get(reverse('membro-list')), reverse('membro-kartaun-hotu'))
