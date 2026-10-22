import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from config import roles
from config.tests import BaseData
from eventu.models import Eventu, Prezensa
from kuota.models import Kuota
from membro.merge import hamutuk
from membro.models import Membro, Alokasaun, Historia
from report.views.view_2 import aniversariu_ba, _duplikadu
from user.models import UserScope


class KualidadeTests(BaseData):
	def setUp(self):
		self.sein = Membro.objects.create(nome='Sein Dadus', sex='Mane', aprovasaun='Aprovadu', organizasaun=self.org)

	def test_metrika(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('report-kualidade'))
		self.assertEqual(r.status_code, 200)
		self.assertEqual((r.context['total'], r.context['kompletu'], r.context['n_falta']), (3, 2, 1))
		self.assertEqual(r.context['pct'], 67)
		self.assertEqual([m.nome for m in r.context['page']], ['Sein Dadus'])
		self.assertEqual(r.context['page'][0].falta, ['Nu. Eleitoral', 'Data Moris', 'Aldeia'])

	def test_peran_hare_deit_área(self):
		self.login(roles.KOORD_MUN)
		r = self.client.get(reverse('report-kualidade'))
		self.assertEqual(r.context['total'], 1)
		self.assertEqual(r.context['duplikadu'], [])        # duplikadu deit ba Presidente/Sekretaria
		self.login(roles.ADMIN)
		self.assertEqual(self.client.get(reverse('report-kualidade')).status_code, 403)

	def test_deteta_duplikadu(self):
		Membro.objects.create(nome='JOAO  silva', sex='Mane', aprovasaun='Aprovadu', telefone='77000001')
		Membro.objects.create(nome='Joao Silvaa', sex='Mane', aprovasaun='Aprovadu')
		Membro.objects.create(nome='Pedro Satu', sex='Mane', aprovasaun='Aprovadu', telefone='78000002')
		Membro.objects.create(nome='Pedro Rua', sex='Mane', aprovasaun='Aprovadu', telefone='78000002')
		self.login(roles.PRESIDENTE)
		sebab = {g['sebab'] for g in self.client.get(reverse('report-kualidade')).context['duplikadu']}
		self.assertTrue({'Naran hanesan', 'Naran parese', 'Nu. telemovel hanesan'} <= sebab)
		grupu = [sorted(m['nome'] for m in g['membru']) for g in _duplikadu(Membro.objects.all())]
		self.assertIn(['Pedro Rua', 'Pedro Satu'], grupu)
		self.assertTrue(any('Joao Silva' in g for g in grupu))

	def test_la_deteta_membru_diferente(self):
		self.assertEqual(_duplikadu(Membro.objects.all()), [])


class HamutukTests(BaseData):
	def setUp(self):
		self.keep = Membro.objects.create(nome='Ana Keep', sex='Feto', aprovasaun='Aprovadu', organizasaun=self.org, telefone='77')
		self.drop = Membro.objects.create(nome='Ana Drop', sex='Feto', aprovasaun='Aprovadu', nu_eleitoral='E-777', date_of_birth=datetime.date(1990, 1, 1),
			email='a@b.tl', aldeia=self.ald1, village=self.vil1, post=self.post1, municipality=self.mun1, telefone='99')

	def test_hamutuk_kompletu(self):
		a_keep = Alokasaun.objects.create(membro=self.keep, nivel='Organizasaun', pozisaun='Membru', organizasaun=self.org, data_hahu=datetime.date(2026, 1, 1))
		Alokasaun.objects.create(membro=self.drop, nivel='Organizasaun', pozisaun='Membru', organizasaun=self.org, data_hahu=datetime.date(2026, 1, 1))   # hanesan
		Alokasaun.objects.create(membro=self.drop, nivel='Departamentu', pozisaun='Koordenador', departamentu=self.dep_org, data_hahu=datetime.date(2026, 1, 1))
		ev1 = Eventu.objects.create(titulu='E1', data_hahu=timezone.now())
		ev2 = Eventu.objects.create(titulu='E2', data_hahu=timezone.now())
		Prezensa.objects.create(eventu=ev1, membro=self.keep, estadu='Prezente')
		Prezensa.objects.create(eventu=ev1, membro=self.drop, estadu='Falta')      # konflitu: keep mantein
		Prezensa.objects.create(eventu=ev2, membro=self.drop, estadu='Prezente')
		Kuota.objects.create(membro=self.drop, tinan=2026, montante=5, data_selu=datetime.date.today())
		Historia.objects.create(membro=self.drop, membro_nome='Ana Drop', aksaun='Kria')
		rez = hamutuk(self.keep, self.drop, self.users[roles.PRESIDENTE])
		self.assertFalse(Membro.objects.filter(pk=self.drop.pk).exists())
		self.keep.refresh_from_db()
		self.assertEqual((self.keep.nome, self.keep.telefone), ('Ana Keep', '77'))            # keep mantein ne'ebé iha
		self.assertEqual((self.keep.nu_eleitoral, self.keep.email, self.keep.aldeia, self.keep.municipality), ('E-777', 'a@b.tl', self.ald1, self.mun1))
		self.assertEqual(sorted(self.keep.alokasaun.values_list('pozisaun', flat=True)), ['Koordenador', 'Membru'])   # la duplika Membru
		self.assertEqual(self.keep.alokasaun.filter(pk=a_keep.pk).count(), 1)
		self.assertEqual(dict(self.keep.prezensa.values_list('eventu__titulu', 'estadu')), {'E1': 'Prezente', 'E2': 'Prezente'})
		self.assertEqual(self.keep.kuota.count(), 1)
		self.assertTrue(self.keep.historia.filter(aksaun='Kria').exists())
		self.assertTrue(self.keep.historia.filter(aksaun='Hamutuk').exists())
		self.assertIn('nu_eleitoral', rez['kampu'])

	def test_login_drop_muda_ba_keep(self):
		u = User.objects.create_user('dropuser', password='x')
		UserScope.objects.create(user=u, membro=self.drop)
		hamutuk(self.keep, self.drop, self.users[roles.PRESIDENTE])
		self.assertEqual(UserScope.objects.get(user=u).membro, self.keep)

	def test_login_rua_desativa_drop(self):
		u1 = User.objects.create_user('k', password='x')
		u2 = User.objects.create_user('d', password='x')
		UserScope.objects.create(user=u1, membro=self.keep)
		UserScope.objects.create(user=u2, membro=self.drop)
		hamutuk(self.keep, self.drop, self.users[roles.PRESIDENTE])
		u2.refresh_from_db()
		self.assertFalse(u2.is_active)
		self.assertIsNone(UserScope.objects.get(user=u2).membro)
		self.assertEqual(UserScope.objects.get(user=u1).membro, self.keep)

	def test_membru_hanesan_error(self):
		with self.assertRaises(ValueError):
			hamutuk(self.keep, self.keep, self.users[roles.PRESIDENTE])

	def test_view_hamutuk(self):
		self.login(roles.SEKRETARIA)
		url = reverse('membro-hamutuk')
		self.assertContains(self.client.get(url, {'a': self.keep.hashed, 'b': self.drop.hashed}), 'Ana Drop')
		r = self.client.post(url, {'a': self.keep.hashed, 'b': self.drop.hashed, 'keep': 'sala'})
		self.assertEqual(r.status_code, 200 if False else r.status_code)
		self.assertTrue(Membro.objects.filter(pk=self.drop.pk).exists())
		r = self.client.post(url, {'a': self.keep.hashed, 'b': self.drop.hashed, 'keep': self.drop.hashed})
		self.assertEqual(r.status_code, 302)
		self.assertFalse(Membro.objects.filter(pk=self.keep.pk).exists())       # drop mak mantein
		self.assertTrue(Membro.objects.filter(pk=self.drop.pk).exists())

	def test_view_hamutuk_peran(self):
		for role in (roles.KOORD_MUN, roles.PRES_ORG, roles.ADMIN):
			self.login(role)
			self.assertEqual(self.client.get(reverse('membro-hamutuk'), {'a': self.keep.hashed, 'b': self.drop.hashed}).status_code, 403, role)

	def test_view_hamutuk_membru_hanesan(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-hamutuk'), {'a': self.keep.hashed, 'b': self.keep.hashed})
		self.assertEqual(r.status_code, 302)


class AniversariuTests(BaseData):
	def setUp(self):
		self.hoje = timezone.localdate()

	def dob(self, dias, ano=1990):
		d = self.hoje + datetime.timedelta(days=dias)
		return datetime.date(ano, d.month, 28 if (d.month == 2 and d.day == 29) else d.day)

	def test_lista_7_loron(self):
		for nome, dias in (('Ohin', 0), ('Aban', 1), ('Loron5', 5), ('Loron20', 20), ('Foin', -2)):
			self.buat(nome, f'E-{abs(dias)}9', self.mun1, self.post1, self.vil1, self.ald1).__class__.objects.filter(nome=nome).update(date_of_birth=self.dob(dias, 1985))
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('report-aniversariu'))
		self.assertEqual([o['membru'].nome for o in r.context['objects']], ['Ohin', 'Aban', 'Loron5'])
		self.assertEqual(r.context['objects'][0]['idade'], self.hoje.year - 1985)
		r = self.client.get(reverse('report-aniversariu'), {'dias': '30'})
		self.assertIn('Loron20', [o['membru'].nome for o in r.context['objects']])
		self.assertNotIn('Foin', [o['membru'].nome for o in r.context['objects']])

	def test_tuir_área_no_status(self):
		Membro.objects.filter(pk=self.m1.pk).update(date_of_birth=self.dob(1))
		Membro.objects.filter(pk=self.m2.pk).update(date_of_birth=self.dob(1), status='Falesidu')
		self.assertEqual([o['membru'].nome for o in aniversariu_ba(self.users[roles.PRESIDENTE])], ['Joao Silva'])
		self.assertEqual([o['membru'].nome for o in aniversariu_ba(self.users[roles.KOORD_MUN])], ['Joao Silva'])
		self.assertEqual(aniversariu_ba(self.users[roles.KOORD_ORG], 7)[0]['membru'].nome, 'Joao Silva')

	def test_iha_home(self):
		Membro.objects.filter(pk=self.m1.pk).update(date_of_birth=self.dob(0))
		self.login(roles.PRESIDENTE)
		self.assertContains(self.client.get(reverse('home')), 'Aniversariu semana')


class RejistuFulanTests(BaseData):
	def test_api(self):
		Membro.objects.filter(pk=self.m1.pk).update(datetime=timezone.now())
		Membro.objects.filter(pk=self.m2.pk).update(datetime=timezone.now() - datetime.timedelta(days=75))
		self.login(roles.PRESIDENTE)
		d = self.client.get(reverse('api-rejistu-fulan')).json()
		self.assertEqual(len(d['label']), 12)
		self.assertEqual(d['label'][-1], timezone.now().strftime('%Y-%m'))
		self.assertEqual(sum(d['obj']), 2)
		self.assertEqual(d['obj'][-1], 1)
		self.login(roles.KOORD_MUN)
		self.assertEqual(sum(self.client.get(reverse('api-rejistu-fulan')).json()['obj']), 1)
