import datetime
from django.urls import reverse
from django.utils import timezone
from config import roles
from config.tests import BaseData
from anunsiu.models import Anunsiu


class AnunsiuTests(BaseData):
	def bikin(self, **kw):
		d = {'titulu': 'Teste', 'mensagem': 'Mensajen', 'audiens': 'Hotu', 'kria_husi': self.users[roles.PRESIDENTE]}
		d.update(kw)
		return Anunsiu.objects.create(**d)

	def titulu(self, role):
		self.login(role)
		return [a.titulu for a in self.client.get(reverse('anunsiu-list')).context['objects']]

	def test_visibilidade_tuir_audiens(self):
		self.bikin(titulu='Hotu')
		self.bikin(titulu='MunDili', audiens='Munisipiu', municipality=self.mun1)
		self.bikin(titulu='MunBau', audiens='Munisipiu', municipality=self.mun2)
		self.bikin(titulu='OrgOJP', audiens='Organizasaun', organizasaun=self.org)
		self.bikin(titulu='OrgOFP', audiens='Organizasaun', organizasaun=self.org2)
		self.bikin(titulu='DepFin', audiens='Departamentu', departamentu=self.dep)
		self.assertEqual(set(self.titulu(roles.PRESIDENTE)), {'Hotu', 'MunDili', 'MunBau', 'OrgOJP', 'OrgOFP', 'DepFin'})
		self.assertEqual(set(self.titulu(roles.KOORD_MUN)), {'Hotu', 'MunDili'})
		self.assertEqual(set(self.titulu(roles.KOORD_SUKU)), {'Hotu', 'MunDili'})       # munisipiu husi suku
		self.assertEqual(set(self.titulu(roles.KOORD_ALDEIA)), {'Hotu', 'MunDili'})
		self.assertEqual(set(self.titulu(roles.PRES_ORG)), {'Hotu', 'OrgOJP'})
		self.assertEqual(set(self.titulu(roles.VICE_ORG)), {'Hotu', 'OrgOJP'})
		self.assertEqual(set(self.titulu(roles.PRES_DEP)), {'Hotu', 'DepFin'})

	def test_orgaun_hare_anunsiu_departamentu_husi_nia_orgaun_deit(self):
		from custom.models import Departamentu
		self.bikin(titulu='DepOrg', audiens='Departamentu', departamentu=self.dep_org)
		# koord_dep ho departamentu orgaun hare anunsiu orgaun
		self.bikin(titulu='OrgOJP', audiens='Organizasaun', organizasaun=self.org)
		u = self.users[roles.KOORD_DEP]
		s = u.scope
		s.departamentu = self.dep_org
		s.save()
		self.assertEqual(set(self.titulu(roles.KOORD_DEP)), {'DepOrg', 'OrgOJP'})

	def test_expira(self):
		hoje = timezone.localdate()
		self.bikin(titulu='Hotu-Foin', data_remata=hoje - datetime.timedelta(days=1))
		self.bikin(titulu='Ativu', data_remata=hoje)
		self.assertEqual(self.titulu(roles.PRESIDENTE), ['Ativu'])

	def test_kria_no_notifika(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('anunsiu-add'), {'titulu': 'Reuniaun', 'mensagem': 'Loron 5', 'audiens': 'Organizasaun', 'organizasaun': self.org.pk})
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		self.assertEqual(self.users[roles.PRES_ORG].notifikasaun.count(), 1)
		self.assertEqual(self.users[roles.SEKR_ORG].notifikasaun.count(), 1)
		self.assertEqual(self.users[roles.KOORD_MUN].notifikasaun.count(), 0)
		self.assertEqual(self.users[roles.PRESIDENTE].notifikasaun.count(), 0)    # kria rasik
		self.assertEqual(self.users[roles.SEKRETARIA].notifikasaun.count(), 1)    # nasionál hatene hotu

	def test_audiens_hotu_notifika_hotu(self):
		self.login(roles.SEKRETARIA)
		self.client.post(reverse('anunsiu-add'), {'titulu': 'PLP', 'mensagem': 'X', 'audiens': 'Hotu'})
		for r in roles.VIEW_ROLES:
			if r != roles.SEKRETARIA:
				self.assertEqual(self.users[r].notifikasaun.count(), 1, r)
		self.assertEqual(self.users[roles.ADMIN].notifikasaun.count(), 0)

	def test_audiens_tenke_target(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('anunsiu-add'), {'titulu': 'X', 'mensagem': 'Y', 'audiens': 'Munisipiu'})
		self.assertEqual(r.status_code, 200)
		self.assertIn('municipality', r.context['form'].errors)

	def test_presidente_orgaun_deit_ba_orgaun_rasik(self):
		self.login(roles.PRES_ORG)
		r = self.client.post(reverse('anunsiu-add'), {'titulu': 'X', 'mensagem': 'Y', 'audiens': 'Hotu'})
		self.assertEqual(r.status_code, 200)
		r = self.client.post(reverse('anunsiu-add'), {'titulu': 'X', 'mensagem': 'Y', 'audiens': 'Organizasaun', 'organizasaun': self.org2.pk})
		self.assertEqual(r.status_code, 200)    # orgaun seluk la iha opsaun
		r = self.client.post(reverse('anunsiu-add'), {'titulu': 'X', 'mensagem': 'Y', 'audiens': 'Organizasaun', 'organizasaun': self.org.pk})
		self.assertEqual(r.status_code, 302)
		self.assertEqual(Anunsiu.objects.get().organizasaun, self.org)

	def test_peran_seluk_la_bele_kria(self):
		for role in (roles.VICE_ORG, roles.SEKR_ORG, roles.KOORD_SUKU, roles.KOORD_DEP, roles.KOORD_ORG):
			self.login(role)
			self.assertEqual(self.client.get(reverse('anunsiu-add')).status_code, 403, role)
			self.assertEqual(self.client.get(reverse('anunsiu-list')).status_code, 200, role)

	def test_edita_hamoos(self):
		a = self.bikin(kria_husi=self.users[roles.PRES_ORG], audiens='Organizasaun', organizasaun=self.org)
		self.login(roles.PRES_DEP)
		self.assertEqual(self.client.get(reverse('anunsiu-update', args=[a.pk])).status_code, 403)
		self.assertEqual(self.client.post(reverse('anunsiu-del', args=[a.pk])).status_code, 403)
		self.login(roles.PRES_ORG)
		self.assertEqual(self.client.get(reverse('anunsiu-update', args=[a.pk])).status_code, 200)
		self.login(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('anunsiu-del', args=[a.pk])).status_code, 403)
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('anunsiu-del', args=[a.pk])).status_code, 302)
		self.assertFalse(Anunsiu.objects.exists())

	def test_iha_iha_home(self):
		self.bikin(titulu='Anunsiu Importante Ida', importante=True)
		self.login(roles.KOORD_SUKU)
		self.assertContains(self.client.get(reverse('home')), 'Anunsiu Importante Ida')
