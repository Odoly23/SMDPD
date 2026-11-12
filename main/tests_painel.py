import datetime
from django.urls import reverse
from config import roles
from config.tests import BaseData
from membro.models import Alokasaun


class PainelTests(BaseData):
	@classmethod
	def setUpTestData(cls):
		super().setUpTestData()
		Alokasaun.objects.create(membro=cls.m1, nivel='Departamentu', pozisaun='Membru', departamentu=cls.dep, ativu='Sim', data_hahu=datetime.date(2024, 1, 1))

	def home(self, role):
		self.login(role)
		r = self.client.get(reverse('home'))
		self.assertEqual(r.status_code, 200)
		return r

	def test_presidente_hare_tudu(self):
		r = self.home(roles.PRESIDENTE)
		for t in ('DILI', 'BAUCAU', 'Finansas', 'Informasaun', 'Organizasaun Juventude', 'Organizasaun Feto', 'Total Membru', 'Liafuan xave'):
			self.assertContains(r, t)
		self.assertEqual(r.context['counts']['total'], 2)
		self.assertEqual(r.context['titulu_area'], 'Munisipiu')

	def test_koord_munisipiu_hare_postu_rasik(self):
		r = self.home(roles.KOORD_MUN)
		self.assertContains(r, 'DOM ALEIXO')
		self.assertNotContains(r, 'BAUCAU VILA')
		self.assertEqual(r.context['counts']['total'], 1)

	def test_koord_postu_hare_suku_rasik(self):
		r = self.home(roles.KOORD_POSTU)
		self.assertContains(r, 'COMORO')
		self.assertNotContains(r, 'BAHU')

	def test_koord_suku_hare_aldeia_rasik(self):
		r = self.home(roles.KOORD_SUKU)
		self.assertContains(r, 'ALDEIA A')
		self.assertNotContains(r, 'ALDEIA B')

	def test_koord_aldeia_hare_sexu(self):
		r = self.home(roles.KOORD_ALDEIA)
		self.assertEqual(r.context['titulu_area'], 'Sexu')
		self.assertEqual([a['total'] for a in r.context['area']], [1, 0])

	def test_pres_departamentu_deit_nia_departamentu(self):
		r = self.home(roles.PRES_DEP)
		self.assertEqual([d['naran'] for d in r.context['departamentus']], ['Finansas'])
		self.assertEqual(r.context['departamentus'][0]['total'], 1)
		self.assertEqual(r.context['orgauns'], [])
		self.assertEqual(r.context['counts']['total'], 1)

	def test_orgaun_deit_nia_orgaun_no_departamentu(self):
		r = self.home(roles.PRES_ORG)
		self.assertEqual([o['naran'] for o in r.context['orgauns']], ['Organizasaun Juventude'])
		self.assertEqual([d['naran'] for d in r.context['departamentus']], ['Finansas (OJP)'])
		self.assertNotContains(r, 'Organizasaun Feto')

	def test_koord_suku_la_hare_membru_seluk_iha_grafik(self):
		r = self.home(roles.KOORD_SUKU)
		self.assertEqual(sum(r.context['grafik_data']), 1)

	def test_filtru_departamentu_iha_lista(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-list') + '?departamentu=%d' % self.dep.pk)
		self.assertContains(r, 'Joao Silva')
		self.assertNotContains(r, 'Maria Costa')

	def test_admin_la_iha_painel(self):
		self.login(roles.ADMIN)
		r = self.client.get(reverse('home'))
		self.assertNotIn('area', r.context)
