import datetime
from decimal import Decimal
from django.urls import reverse
from config import roles
from config.tests import BaseData
from kuota.models import Kuota

TINAN = datetime.date.today().year


class KuotaTests(BaseData):
	def selu(self, membro, montante='5.00', tinan=TINAN, user=None, **kw):
		return Kuota.objects.create(membro=membro, tinan=tinan, montante=Decimal(montante), data_selu=datetime.date.today(),
			rejistu_husi=user or self.users[roles.SEKRETARIA], **kw)

	def dados(self, membro, **kw):
		d = {'membro': membro.pk, 'tinan': TINAN, 'montante': '10.00', 'data_selu': datetime.date.today().isoformat(), 'metodu': 'Kontante'}
		d.update(kw)
		return d

	def test_rejistu_no_historia(self):
		self.login(roles.SEKRETARIA)
		r = self.client.post(reverse('kuota-add'), self.dados(self.m1))
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		k = Kuota.objects.get()
		self.assertEqual((k.membro, k.montante, k.rejistu_husi), (self.m1, Decimal('10.00'), self.users[roles.SEKRETARIA]))
		self.assertTrue(self.m1.historia.filter(aksaun='Kuota').exists())

	def test_montante_no_tinan_la_loos(self):
		self.login(roles.SEKRETARIA)
		for kw in ({'montante': '0'}, {'montante': '-5'}, {'tinan': 1990}, {'tinan': TINAN + 5}):
			r = self.client.post(reverse('kuota-add'), self.dados(self.m1, **kw))
			self.assertEqual(r.status_code, 200, kw)
		self.assertEqual(Kuota.objects.count(), 0)

	def test_membru_tenke_iha_área(self):
		self.login(roles.KOORD_SUKU)
		r = self.client.post(reverse('kuota-add'), self.dados(self.m2))
		self.assertEqual(r.status_code, 200)
		self.assertIn('membro', r.context['form'].errors)
		pend = self.buat('Pend', 'E-5', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.assertEqual(self.client.post(reverse('kuota-add'), self.dados(pend)).status_code, 200)
		self.assertEqual(Kuota.objects.count(), 0)

	def test_peran(self):
		for role in (roles.PRESIDENTE, roles.VICE_ORG, roles.PRES_ORG, roles.PRES_DEP, roles.ADMIN):
			self.login(role)
			self.assertEqual(self.client.get(reverse('kuota-add')).status_code, 403, role)
		for role in (roles.PRESIDENTE, roles.VICE_ORG, roles.KOORD_MUN):
			self.login(role)
			self.assertEqual(self.client.get(reverse('kuota-list')).status_code, 200, role)
			self.assertEqual(self.client.get(reverse('kuota-rezumu')).status_code, 200, role)
		self.login(roles.ADMIN)
		self.assertEqual(self.client.get(reverse('kuota-list')).status_code, 403)

	def test_lista_tuir_área_no_tinan(self):
		self.selu(self.m1)
		self.selu(self.m2, '7.50')
		self.selu(self.m1, '3.00', tinan=TINAN - 1)
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('kuota-list'))
		self.assertEqual(r.context['total'], Decimal('12.50'))
		self.assertEqual(r.context['n_membru'], 2)
		self.login(roles.KOORD_MUN)
		r = self.client.get(reverse('kuota-list'))
		self.assertEqual(r.context['total'], Decimal('5.00'))
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.get(reverse('kuota-list'), {'tinan': TINAN - 1}).context['total'], Decimal('3.00'))

	def test_membru_selu_barak_dala(self):
		self.selu(self.m1, '2.00')
		self.selu(self.m1, '3.00')
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('kuota-list'))
		self.assertEqual((r.context['total'], r.context['n_membru']), (Decimal('5.00'), 1))

	def test_rezumu(self):
		self.selu(self.m1, '4.00')
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('kuota-rezumu'))
		self.assertEqual((r.context['n_ativu'], r.context['n_selu'], r.context['pct'], r.context['total']), (2, 1, 50, Decimal('4.00')))
		por = {x['naran']: x for x in r.context['por_mun']}
		self.assertEqual((por['Dili']['pct'], por['Baucau']['pct']), (100, 0))
		self.assertEqual([m.nome for m in r.context['page']], ['Maria Costa'])
		csv = self.client.get(reverse('kuota-rezumu'), {'export': 'csv'})
		self.assertContains(csv, 'Maria Costa')
		self.assertNotContains(csv, 'Joao Silva')

	def test_csv_lista(self):
		self.selu(self.m1)
		self.login(roles.PRESIDENTE)
		self.assertContains(self.client.get(reverse('kuota-list'), {'export': 'csv'}), 'Joao Silva')

	def test_hamoos(self):
		k = self.selu(self.m1, user=self.users[roles.SEKRETARIA])
		self.login(roles.KOORD_MUN)
		self.assertEqual(self.client.post(reverse('kuota-del', args=[k.pk])).status_code, 403)      # la rejistu rasik
		self.login(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('kuota-del', args=[k.pk])).status_code, 302)
		self.assertEqual(Kuota.objects.count(), 0)
		k2 = self.selu(self.m2)
		self.login(roles.KOORD_MUN)
		self.assertEqual(self.client.post(reverse('kuota-del', args=[k2.pk])).status_code, 404)     # laiha iha área
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('kuota-del', args=[k2.pk])).status_code, 302)

	def test_search(self):
		self.login(roles.KOORD_MUN)
		r = self.client.get(reverse('kuota-search'), {'q': 'silva'})
		self.assertContains(r, 'Joao Silva')
		self.assertNotContains(self.client.get(reverse('kuota-search'), {'q': 'costa'}), 'Maria')
