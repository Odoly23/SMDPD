import datetime
from django.urls import reverse
from django.utils import timezone
from config import roles
from config.tests import BaseData
from custom.models import Departamentu
from main.views import MODAL_MAKS_DEP, MODAL_MAKS_LIDER
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


class ModalEntidadeTests(BaseData):
	def test_entidade_simples_uza_modal(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('home'))
		self.assertContains(r, 'id="modal-entidade"')
		self.assertContains(r, 'data-modal="%s?modal=1"' % reverse('entidade-orgaun', args=[self.org.hashed]))
		self.assertTrue(all(e['modal'] for e in r.context['entidades']))

	def test_entidade_kompleksu_la_uza_modal(self):
		for i in range(MODAL_MAKS_DEP + 1):
			Departamentu.objects.create(code='D%d' % i, name='Dep %d' % i, organizasaun=self.org2)
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('home'))
		por_naran = {e['naran']: e['modal'] for e in r.context['entidades']}
		self.assertFalse(por_naran['Organizasaun Feto'])
		self.assertTrue(por_naran['Organizasaun Juventude'])
		url = reverse('entidade-orgaun', args=[self.org2.hashed])
		self.assertNotContains(r, 'data-modal="%s?modal=1"' % url)
		self.assertContains(r, 'href="%s"' % url)

	def test_entidade_kompleksu_tanba_lideransa_barak(self):
		for i in range(MODAL_MAKS_LIDER + 1):
			m = self.buat('Lider %d' % i, 'E-7%03d' % i, self.mun1, self.post1, self.vil1, self.ald1)
			Alokasaun.objects.create(membro=m, nivel='Organizasaun', pozisaun='Koordenador', organizasaun=self.org2, ativu='Sim', data_hahu=HOJE)
		self.login(roles.PRESIDENTE)
		por_naran = {e['naran']: e['modal'] for e in self.client.get(reverse('home')).context['entidades']}
		self.assertFalse(por_naran['Organizasaun Feto'])

	def test_modac_iha_seed(self):
		from config.management.commands.seed_inisial import ORGAUN
		self.assertIn(('MODAC', 'MODAC'), ORGAUN)

	def test_fragmentu_modal_la_iha_layout(self):
		Alokasaun.objects.create(membro=self.m1, nivel='Organizasaun', pozisaun='Presidente', organizasaun=self.org, ativu='Sim', data_hahu=HOJE)
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('entidade-orgaun', args=[self.org.hashed]) + '?modal=1')
		self.assertEqual(r.status_code, 200)
		self.assertContains(r, 'Joao Silva')
		self.assertContains(r, 'DEPARTAMENTU')
		self.assertNotContains(r, '<html')
		self.assertNotContains(r, 'topbar')

	def test_modal_tuir_peran(self):
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.get(reverse('entidade-orgaun', args=[self.org2.hashed]) + '?modal=1').status_code, 404)
		self.client.logout()
		self.assertEqual(self.client.get(reverse('entidade-nasional') + '?modal=1').status_code, 302)


import shutil, tempfile
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings


def _png():
	b = BytesIO()
	Image.new('RGB', (200, 240), (200, 30, 30)).save(b, 'PNG')
	return SimpleUploadedFile('foto.png', b.getvalue(), content_type='image/png')


class FotuKartaunTests(BaseData):
	@classmethod
	def setUpClass(cls):
		cls._tmp = tempfile.mkdtemp()
		cls._ov = override_settings(PRIVATE_MEDIA_ROOT=cls._tmp)
		cls._ov.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._ov.disable()
		shutil.rmtree(cls._tmp, ignore_errors=True)

	def setUp(self):
		self.m1.image.save('foto.png', _png(), save=True)

	def test_kartaun_individual_ho_fotu(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-kartaun', args=[self.m1.hashed]))
		self.assertContains(r, reverse('membro-fotu', args=[self.m1.hashed]))
		self.assertNotContains(r, 'seidauk iha fotu')
		f = self.client.get(reverse('membro-fotu', args=[self.m1.hashed]))
		self.assertEqual(f.status_code, 200)
		self.assertEqual(f['Content-Type'], 'image/png')
		self.assertEqual(self.client.get(reverse('membro-kartaun', args=[self.m1.hashed]) + '?cetak=1').status_code, 200)

	def test_kartaun_sein_fotu_hatudu_avizu(self):
		self.login(roles.SEKRETARIA)
		r = self.client.get(reverse('membro-kartaun', args=[self.m2.hashed]))
		self.assertContains(r, 'seidauk iha fotu')
		self.assertContains(r, reverse('membro-update', args=[self.m2.hashed]))

	def test_kartaun_hotu_ho_fotu_no_filtru(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-kartaun-hotu'), {'cetak': 1})
		self.assertContains(r, reverse('membro-fotu', args=[self.m1.hashed]))
		self.assertNotContains(r, reverse('membro-fotu', args=[self.m2.hashed]))   # m2 laiha fotu: kuadru mamuk
		r = self.client.get(reverse('membro-kartaun-hotu'))
		self.assertEqual(r.context['sen_fotu'], 1)
		self.assertContains(r, 'seidauk iha fotu')
		r = self.client.get(reverse('membro-kartaun-hotu'), {'fotu': 'iha'})
		self.assertEqual([c['obj'].nome for f in r.context['folhas'] for c in f], ['Joao Silva'])
		r = self.client.get(reverse('membro-kartaun-hotu'), {'fotu': 'laiha'})
		self.assertEqual([c['obj'].nome for f in r.context['folhas'] for c in f], ['Maria Costa'])

	def test_fotu_la_bele_hare_membru_área_seluk(self):
		self.login(roles.KOORD_SUKU)                      # suku Comoro: m1 sim, m2 lae
		self.assertEqual(self.client.get(reverse('membro-fotu', args=[self.m1.hashed])).status_code, 200)
		self.m2.image.save('foto2.png', _png(), save=True)
		self.assertEqual(self.client.get(reverse('membro-fotu', args=[self.m2.hashed])).status_code, 404)

	def test_kartaun_la_uza_background_image_ba_imajen(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-kartaun', args=[self.m1.hashed]))
		self.assertContains(r, 'k-kotuk-bg')
		self.assertNotContains(r, 'background-image')


class LogoOrgaunTests(BaseData):
	@classmethod
	def setUpClass(cls):
		cls._media = tempfile.mkdtemp()
		cls._ov = override_settings(MEDIA_ROOT=cls._media)
		cls._ov.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._ov.disable()
		shutil.rmtree(cls._media, ignore_errors=True)

	def kartaun(self, m, **extra):
		self.login(roles.PRESIDENTE)
		return self.client.get(reverse('membro-kartaun', args=[m.hashed]), extra)

	def test_kartaun_membru_orgaun_ho_logo_karuk_no_plp_los(self):
		self.org.logo.save('logo.png', _png(), save=True)
		html = self.kartaun(self.m1).content.decode('utf-8')           # m1 = membru orgaun OJP
		kiri = html.index('k-flag-kiri'); kanan = html.index('k-flag-kanan')
		self.assertLess(kiri, kanan)
		self.assertIn(self.org.logo.url, html[kiri:kanan])             # logo orgaun iha karuk
		self.assertIn('logo_plp.png', html[kanan:html.index('k-t1')])  # logo PLP iha los
		self.assertNotIn('bandeira_plp.jpg" alt="PLP"', html[kiri:kanan])

	def test_kartaun_orgaun_sein_logo_hatudu_kodigu(self):
		html = self.kartaun(self.m1).content.decode('utf-8')
		kiri = html[html.index('k-flag-kiri'):html.index('k-flag-kanan')]
		self.assertIn('k-org-kode', kiri)
		self.assertIn('>OJP<', kiri)

	def test_kartaun_membru_sein_orgaun_hanesan_modelu(self):
		html = self.kartaun(self.m2).content.decode('utf-8')           # m2 laiha orgaun
		kiri = html[html.index('k-flag-kiri'):html.index('k-flag-kanan')]
		self.assertIn('bandeira_plp.jpg', kiri)
		self.assertNotIn('k-org', kiri)

	def test_kartaun_hotu_logo_orgaun_tuir_membru(self):
		self.org.logo.save('logo.png', _png(), save=True)
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-kartaun-hotu'), {'cetak': 1})
		html = r.content.decode('utf-8')
		self.assertEqual(html.count(self.org.logo.url), 1)             # m1 deit; m2 laiha orgaun
		self.assertEqual(html.count('k-emblema-logo'), 2)              # logo PLP iha los iha kartaun hotu

	def test_varanda_logo_orgaun_rasik_no_kodigu(self):
		self.org.logo.save('logo.png', _png(), save=True)
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('home'))
		por = {e['naran']: e for e in r.context['entidades']}
		self.assertEqual(por['Organizasaun Juventude']['logo'], self.org.logo.url)
		self.assertIsNone(por['Organizasaun Feto']['logo'])
		self.assertEqual(por['Organizasaun Feto']['kode'], 'OFP')
		self.assertContains(r, 'class="logo-kode"')
		self.assertContains(r, self.org.logo.url)
		self.assertTrue(por['PLP Nasionál']['logo'].endswith('logo_plp.png'))

	def test_detallu_orgaun_logo(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('entidade-orgaun', args=[self.org.hashed]))
		self.assertContains(r, 'logo-kode')                            # seidauk iha logo: kódigu OJP
		self.org.logo.save('logo.png', _png(), save=True)
		r = self.client.get(reverse('entidade-orgaun', args=[self.org.hashed]))
		self.assertContains(r, self.org.logo.url)


class MediaPublikuTests(BaseData):
	"""/media/ sai husi Django (deploy): logo orgaun públiku; la bele sai fotu membru ka file seluk."""
	@classmethod
	def setUpClass(cls):
		cls._media = tempfile.mkdtemp()
		cls._ov = override_settings(MEDIA_ROOT=cls._media)
		cls._ov.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._ov.disable()
		shutil.rmtree(cls._media, ignore_errors=True)

	def test_logo_orgaun_bele_loke_sein_login(self):
		self.org.logo.save('logo.png', _png(), save=True)
		r = self.client.get(self.org.logo.url)
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r['Content-Type'], 'image/png')

	def test_la_bele_sai_file_seluk(self):
		for path in ('/media/../manage.py', '/media/%2e%2e/manage.py', '/media/..%2f..%2f.env', '/media/', '/media/membro_foto/x.png'):
			self.assertIn(self.client.get(path).status_code, (400, 404), path)      # tolak (la 200)

	def test_fotu_membru_la_iha_iha_media(self):
		from django.conf import settings
		self.assertNotEqual(settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_ROOT)
