import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from config import roles
from config.tests import BaseData
from membro.models import Membro


def csv_file(texto, nome='membru.csv'):
	return SimpleUploadedFile(nome, texto.encode('utf-8'), content_type='text/csv')


class ImportTests(BaseData):
	HEADER = 'nome,sex,date_of_birth,nu_eleitoral,aldeia_code,organizasaun_code\n'

	def setUp(self):
		self.ald1.code, self.ald2.code = 'DIL-A1', 'BAU-A1'
		self.ald1.save(); self.ald2.save()

	def post(self, texto, verifika=False):
		d = {'arkivu': csv_file(texto)}
		if verifika:
			d['verifika'] = 'on'
		return self.client.post(reverse('membro-import'), d)

	def test_import_susesu(self):
		self.login(roles.SEKRETARIA)
		r = self.post(self.HEADER + 'Ana Maria,feto,15/03/1992,EL-5001,DIL-A1,OJP\nPedro,Mane,1980-01-02,el-5002,BAU-A1,\n')
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context.get('erru'))
		a = Membro.objects.get(nu_eleitoral='EL-5001')
		self.assertEqual((a.nome, a.sex, a.aprovasaun, str(a.date_of_birth)), ('Ana Maria', 'Feto', 'Pendente', '1992-03-15'))
		self.assertEqual((a.municipality, a.post, a.village, a.aldeia, a.organizasaun), (self.mun1, self.post1, self.vil1, self.ald1, self.org))
		self.assertTrue(Membro.objects.filter(nu_eleitoral='EL-5002').exists())
		self.assertEqual(self.users[roles.PRESIDENTE].notifikasaun.count(), 1)

	def test_verifika_la_rai(self):
		self.login(roles.SEKRETARIA)
		r = self.post(self.HEADER + 'Ana,Feto,1992-03-15,EL-5001,DIL-A1,\n', verifika=True)
		self.assertEqual(r.status_code, 200)
		self.assertFalse(Membro.objects.filter(nu_eleitoral='EL-5001').exists())

	def test_tudu_ka_laiha(self):
		self.login(roles.SEKRETARIA)
		r = self.post(self.HEADER + 'Ana,Feto,1992-03-15,EL-5001,DIL-A1,\nRuim,Mane,2999-01-01,EL-5002,DIL-A1,\nDuplikadu,Mane,1990-01-01,E-0001,DIL-A1,\nSein,Mane,1990-01-01,EL-5003,XXX,\n')
		self.assertEqual(r.status_code, 200)
		self.assertEqual({e['linha'] for e in r.context['erru']}, {3, 4, 5})
		self.assertFalse(Membro.objects.filter(nu_eleitoral__in=['EL-5001', 'EL-5002', 'EL-5003']).exists())

	def test_repete_iha_file(self):
		self.login(roles.SEKRETARIA)
		r = self.post(self.HEADER + 'A,Mane,1990-01-01,EL-5001,DIL-A1,\nB,Mane,1991-01-01,el-5001,DIL-A1,\n')
		self.assertEqual(r.status_code, 200)
		self.assertEqual([e['linha'] for e in r.context['erru']], [3])
		self.assertEqual(Membro.objects.filter(nu_eleitoral='EL-5001').count(), 0)

	def test_koord_suku_la_bele_importa_suku_seluk(self):
		self.login(roles.KOORD_SUKU)
		r = self.post(self.HEADER + 'Ana,Feto,1992-03-15,EL-5001,BAU-A1,\n')
		self.assertEqual(r.status_code, 200)
		self.assertEqual(len(r.context['erru']), 1)
		r = self.post(self.HEADER + 'Ana,Feto,1992-03-15,EL-5001,DIL-A1,\n')
		self.assertEqual(r.status_code, 302)

	def test_koluna_falta_no_file_mamuk(self):
		self.login(roles.SEKRETARIA)
		r = self.post('nome,sex\nAna,Feto\n')
		self.assertContains(r, 'Koluna obrigat')
		r = self.post(self.HEADER)
		self.assertContains(r, 'File mamuk')

	def test_semikolon_no_peran(self):
		self.login(roles.SEKRETARIA)
		r = self.post('nome;sex;date_of_birth;nu_eleitoral;aldeia_code\nAna;Feto;1992-03-15;EL-5001;DIL-A1\n')
		self.assertEqual(r.status_code, 302)
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.get(reverse('membro-import')).status_code, 403)
		self.login(roles.VICE_ORG)
		self.assertEqual(self.client.get(reverse('membro-import-template')).status_code, 403)

	def test_modelu_download(self):
		self.login(roles.SEKRETARIA)
		r = self.client.get(reverse('membro-import-template'))
		self.assertContains(r, 'nu_eleitoral')


class KartaunTests(BaseData):
	def test_kartaun_aprovadu(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-kartaun', args=[self.m1.hashed]))
		self.assertContains(r, 'Joao Silva')
		self.assertContains(r, 'E-0001')

	def test_kartaun_pendente_404(self):
		p = self.buat('Pendente', 'E-9100', self.mun1, self.post1, self.vil1, self.ald1, aprovasaun='Pendente')
		self.login(roles.PRESIDENTE)
		self.assertEqual(self.client.get(reverse('membro-kartaun', args=[p.hashed])).status_code, 404)

	def test_kartaun_la_bele_hare_area_seluk(self):
		self.login(roles.KOORD_SUKU)
		self.assertEqual(self.client.get(reverse('membro-kartaun', args=[self.m2.hashed])).status_code, 404)

	def test_detail_iha_botaun_kartaun(self):
		self.login(roles.PRESIDENTE)
		self.assertContains(self.client.get(reverse('membro-detail', args=[self.m1.hashed])), '/kartaun/')


class UIFiturTests(BaseData):
	def test_modal_konfirmasaun_iha_layout(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-detail', args=[self.m1.hashed]))
		self.assertContains(r, 'modal-konfirma')
		self.assertContains(r, 'data-confirm')
		self.assertNotContains(r, 'onsubmit="return confirm')

	def test_lista_ho_data_label(self):
		self.login(roles.PRESIDENTE)
		r = self.client.get(reverse('membro-list'))
		self.assertContains(r, 'table-stack')
		self.assertContains(r, 'data-label="Naran"')
