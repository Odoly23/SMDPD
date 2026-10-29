import datetime
from django.urls import reverse
from django.utils import timezone
from config import roles
from config.tests import BaseData
from eventu.models import Eventu, Prezensa
from eventu.utils import eventu_ba, pool_membru


class EventuTests(BaseData):
	def dados(self, **kw):
		d = {'titulu': 'Reuniaun Mensál', 'tipu': 'Reuniaun', 'data_hahu': (timezone.now() + datetime.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'), 'fatin': 'Dili'}
		d.update(kw)
		return d

	def kria(self, role, **kw):
		self.login(role)
		r = self.client.post(reverse('eventu-add'), self.dados(**kw))
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		return Eventu.objects.latest('pk')

	def test_area_eventu_tuir_kria_husi(self):
		n = self.kria(roles.PRESIDENTE, titulu='Nas')
		m = self.kria(roles.KOORD_MUN, titulu='Mun')
		o = self.kria(roles.PRES_ORG, titulu='Org')
		d = self.kria(roles.PRES_DEP, titulu='Dep')
		a = self.kria(roles.KOORD_ALDEIA, titulu='Ald')
		self.assertEqual((n.municipality, n.organizasaun, n.departamentu), (None, None, None))
		self.assertEqual(m.municipality, self.mun1)
		self.assertEqual(o.organizasaun, self.org)
		self.assertEqual(d.departamentu, self.dep)
		self.assertEqual(a.aldeia, self.ald1)
		self.assertEqual(str(n.unidade()), 'PLP Nasionál')

	def test_visibilidade(self):
		self.kria(roles.PRESIDENTE, titulu='Nas')
		self.kria(roles.KOORD_MUN, titulu='Mun')
		self.kria(roles.PRES_ORG, titulu='Org')
		self.kria(roles.KOORD_ALDEIA, titulu='Ald')
		def titulu(role):
			return {e.titulu for e in eventu_ba(self.users[role])}
		self.assertEqual(titulu(roles.PRESIDENTE), {'Nas', 'Mun', 'Org', 'Ald'})
		self.assertEqual(titulu(roles.KOORD_MUN), {'Nas', 'Mun'})
		self.assertEqual(titulu(roles.KOORD_SUKU), {'Nas', 'Mun'})            # munisipiu husi área geográfika
		self.assertEqual(titulu(roles.KOORD_ALDEIA), {'Nas', 'Mun', 'Ald'})
		self.assertEqual(titulu(roles.VICE_ORG), {'Nas', 'Org'})
		self.assertEqual(titulu(roles.PRES_DEP), {'Nas'})

	def test_peran_la_bele_kria(self):
		for role in (roles.VICE_ORG, roles.ADMIN):
			self.login(role)
			self.assertEqual(self.client.get(reverse('eventu-add')).status_code, 403, role)

	def test_lista_tab(self):
		agora = timezone.now()
		self.client.force_login(self.users[roles.PRESIDENTE])
		Eventu.objects.create(titulu='Futuru', data_hahu=agora + datetime.timedelta(days=1), kria_husi=self.users[roles.PRESIDENTE])
		Eventu.objects.create(titulu='Liu', data_hahu=agora - datetime.timedelta(days=1), kria_husi=self.users[roles.PRESIDENTE])
		self.assertEqual([e.titulu for e in self.client.get(reverse('eventu-list')).context['objects']], ['Futuru'])
		self.assertEqual([e.titulu for e in self.client.get(reverse('eventu-list'), {'tab': 'liu'}).context['objects']], ['Liu'])

	def test_data_remata_antes_hahu(self):
		self.login(roles.PRESIDENTE)
		r = self.client.post(reverse('eventu-add'), self.dados(data_remata=(timezone.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')))
		self.assertEqual(r.status_code, 200)
		self.assertIn('data_remata', r.context['form'].errors)

	def test_edita_hamoos_deit_kria_husi_ka_presidente(self):
		ev = self.kria(roles.KOORD_MUN)
		self.login(roles.KOORD_ORG)
		self.assertEqual(self.client.get(reverse('eventu-update', args=[ev.pk])).status_code, 404)  # la hare
		self.login(roles.KOORD_POSTU)
		self.assertEqual(self.client.get(reverse('eventu-update', args=[ev.pk])).status_code, 403)  # hare maibé la kria rasik
		self.login(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('eventu-del', args=[ev.pk])).status_code, 403)
		self.login(roles.KOORD_MUN)
		self.assertEqual(self.client.get(reverse('eventu-update', args=[ev.pk])).status_code, 200)
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.post(reverse('eventu-del', args=[ev.pk])).status_code, 302)
		self.assertFalse(Eventu.objects.exists())


class PrezensaTests(BaseData):
	def setUp(self):
		self.ev_nas = Eventu.objects.create(titulu='Nas', data_hahu=timezone.now(), kria_husi=self.users[roles.PRESIDENTE])
		self.ev_dili = Eventu.objects.create(titulu='Dili', data_hahu=timezone.now(), kria_husi=self.users[roles.KOORD_MUN], municipality=self.mun1)

	def test_pool_tuir_area_eventu_no_uzuariu(self):
		self.assertEqual({m.nome for m in pool_membru(self.users[roles.PRESIDENTE], self.ev_nas)}, {'Joao Silva', 'Maria Costa'})
		self.assertEqual({m.nome for m in pool_membru(self.users[roles.PRESIDENTE], self.ev_dili)}, {'Joao Silva'})
		self.assertEqual({m.nome for m in pool_membru(self.users[roles.KOORD_MUN], self.ev_nas)}, {'Joao Silva'})   # área uzuáriu
		pend = self.buat('Pend', 'E-9', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.assertNotIn(pend, pool_membru(self.users[roles.PRESIDENTE], self.ev_nas))

	def test_foti_prezensa(self):
		self.login(roles.PRESIDENTE)
		url = reverse('prezensa-foti', args=[self.ev_nas.pk])
		self.assertContains(self.client.get(url), 'Joao Silva')
		r = self.client.post(url, {'membro_id': [self.m1.pk, self.m2.pk], f'estadu_{self.m1.pk}': 'Prezente', f'estadu_{self.m2.pk}': 'Lisensa'})
		self.assertEqual(r.status_code, 302)
		self.assertEqual(dict(Prezensa.objects.values_list('membro__nome', 'estadu')), {'Joao Silva': 'Prezente', 'Maria Costa': 'Lisensa'})
		self.client.post(url, {'membro_id': [self.m2.pk], f'estadu_{self.m2.pk}': '-'})
		self.assertEqual(Prezensa.objects.count(), 1)
		self.client.post(url, {'membro_id': [self.m1.pk], f'estadu_{self.m1.pk}': 'Falta'})
		self.assertEqual(Prezensa.objects.get().estadu, 'Falta')                      # atualiza, la duplika

	def test_la_bele_foti_membru_sai_husi_pool(self):
		self.login(roles.KOORD_MUN)
		url = reverse('prezensa-foti', args=[self.ev_dili.pk])
		self.client.post(url, {'membro_id': [self.m2.pk], f'estadu_{self.m2.pk}': 'Prezente'})      # Baucau: la valid
		self.assertEqual(Prezensa.objects.count(), 0)
		self.client.post(url, {'membro_id': [self.m1.pk], f'estadu_{self.m1.pk}': 'XXX'})            # estadu sala
		self.assertEqual(Prezensa.objects.count(), 0)

	def test_prezensa_rapidu(self):
		self.login(roles.PRESIDENTE)
		url = reverse('prezensa-rapidu', args=[self.ev_nas.pk])
		self.client.post(url, {'nu_eleitoral': ' e-0002 '})
		self.assertEqual(Prezensa.objects.get().membro, self.m2)
		r = self.client.post(url, {'nu_eleitoral': 'laiha'}, follow=True)
		self.assertContains(r, 'la hetan')
		self.assertEqual(Prezensa.objects.count(), 1)

	def test_filtru_no_paginasaun(self):
		self.login(roles.PRESIDENTE)
		Prezensa.objects.create(eventu=self.ev_nas, membro=self.m1, estadu='Prezente')
		r = self.client.get(reverse('prezensa-foti', args=[self.ev_nas.pk]), {'hira': 'seidauk'})
		self.assertEqual([m.nome for m in r.context['page']], ['Maria Costa'])
		r = self.client.get(reverse('prezensa-foti', args=[self.ev_nas.pk]), {'q': 'joao'})
		self.assertEqual([m.estadu_atual for m in r.context['page']], ['Prezente'])

	def test_detail_no_csv_no_membru(self):
		Prezensa.objects.create(eventu=self.ev_nas, membro=self.m1, estadu='Prezente')
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('eventu-detail', args=[self.ev_nas.pk]))
		self.assertEqual(r.context['total']['Prezente'], 1)
		csvr = self.client.get(reverse('prezensa-csv', args=[self.ev_nas.pk]))
		self.assertContains(csvr, 'Joao Silva')
		self.assertContains(self.client.get(reverse('membro-detail', args=[self.m1.hashed])), 'Prezensa iha Eventu')

	def test_peran_seluk_la_bele_foti(self):
		self.login(roles.VICE_ORG)
		self.assertEqual(self.client.get(reverse('prezensa-foti', args=[self.ev_nas.pk])).status_code, 403)
		self.assertEqual(self.client.get(reverse('eventu-detail', args=[self.ev_nas.pk])).status_code, 200)
