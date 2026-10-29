"""Auditoria seguransa: otorizasaun hotu-hotu, CSV injection, XSS, fotu privadu, upload, redirect, CSRF, sesaun."""
import io
import os
import re
import runpy
import shutil
import tempfile
from unittest import mock
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.urls import get_resolver, reverse
from PIL import Image
from config import roles
from config.tests import BaseData
from membro.models import Membro

PASS = 'x-Senha-123'
XSS = '<script>alert(1)</script>'
LIBRE = {'login', 'login-2fa'}          # pájina públiku (login)


def hatama_url():
	"""Lista (naran, path) husi URL hotu iha projetu (ho argumentu dummy), la inklui admin Django."""
	hasil = []

	def jalan(patterns, prefix):
		for p in patterns:
			parte = str(p.pattern)
			if hasattr(p, 'url_patterns'):
				if parte.startswith(('admin', 'static', 'media')):
					continue
				jalan(p.url_patterns, prefix + parte)
			else:
				path = '/' + prefix + parte
				path = re.sub(r'<int:\w+>', '1', path)
				path = re.sub(r'<(?:str|slug):\w+>', 'x', path)
				path = re.sub(r'<\w+>', 'x', path)
				hasil.append((p.name, path))

	jalan(get_resolver().url_patterns, '')
	return hasil


URLS = hatama_url()


def gambar_bytes(w=40, h=40, formatu='PNG'):
	buf = io.BytesIO()
	Image.new('RGB', (w, h), (10, 120, 200)).save(buf, formatu)
	return buf.getvalue()


class OtorizasaunTests(BaseData):
	def test_url_la_vazia(self):
		self.assertGreater(len(URLS), 60)

	def test_anonimu_la_bele_aksesu_buat_ida(self):
		c = Client()
		for nama, path in URLS:
			if nama in LIBRE:
				continue
			for metodu in ('get', 'post'):
				r = getattr(c, metodu)(path)
				if nama == 'logout' and metodu == 'get':
					self.assertEqual(r.status_code, 405)              # logout POST deit
					continue
				if nama.startswith('api-'):
					self.assertIn(r.status_code, (401, 403), f'{path} -> {r.status_code}')   # DRF: la hatudu data ba anonimu
					continue
				self.assertEqual(r.status_code, 302, f'{metodu.upper()} {path} ({nama}) -> {r.status_code}')
				self.assertTrue(r['Location'].startswith('/login/') or r['Location'].startswith('/admin'), f'{path}: {r["Location"]}')

	def test_pájina_login_públiku_deit(self):
		c = Client()
		self.assertEqual(c.get(reverse('login')).status_code, 200)
		self.assertEqual(c.get(reverse('login-2fa')).status_code, 302)       # sein pre-autentikasaun

	def test_la_iha_error_500_iha_peran_ida(self):
		"""Peran hotu x URL hotu x GET/POST mamuk: laiha 500 (validasaun input robusta)."""
		for role in list(self.users):
			self.client.force_login(self.users[role])
			for nama, path in URLS:
				if nama in ('logout', 'sai-hotu'):
					continue
				for metodu in ('get', 'post'):
					r = getattr(self.client, metodu)(path)
					self.assertLess(r.status_code, 500, f'{role} {metodu.upper()} {path} ({nama}) -> {r.status_code}')

	def test_peran_la_bele_aksesu_pájina_admin(self):
		admin_nama = {'user-list', 'user-add', 'user-update', 'user-reset', 'user-reset-2fa', 'user-log', 'master-list', 'master-add', 'master-update', 'master-del'}
		for role in self.users:
			if role == roles.ADMIN:
				continue
			self.client.force_login(self.users[role])
			for nama, path in URLS:
				if nama in admin_nama:
					for metodu in ('get', 'post'):
						self.assertEqual(getattr(self.client, metodu)(path).status_code, 403, f'{role} {metodu.upper()} {path}')

	def test_django_admin_la_loke_ba_ema_ida(self):
		for role in self.users:
			self.client.force_login(self.users[role])
			r = self.client.get('/admin/')
			self.assertEqual(r.status_code, 302, role)
			self.assertIn('/admin/login/', r['Location'])

	def test_csrf_obrigatóriu(self):
		c = Client(enforce_csrf_checks=True)
		c.force_login(self.users[roles.PRESIDENTE])
		for nama, path in [('membro-del', f'/membro/{self.m1.hashed}/del/'), ('aprovasaun-bulk', '/membro/aprovasaun/bulk/'), ('logout', '/logout/'),
				('notif-le', '/notif/le/'), ('sai-hotu', '/seguransa/sai-hotu/')]:
			self.assertEqual(c.post(path).status_code, 403, nama)
		self.assertTrue(Membro.objects.filter(pk=self.m1.pk).exists())
		self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('login'), {'username': 'a', 'password': 'b'}).status_code, 403)

	def test_mutasaun_ho_get_la_bele(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		antes = Membro.objects.count()
		for path in (f'/membro/{self.m1.hashed}/del/', '/membro/aprovasaun/bulk/', f'/membro/aprovasaun/{self.m1.hashed}/aprova/'):
			self.assertIn(self.client.get(path).status_code, (403, 404, 405, 302))
		self.assertEqual(Membro.objects.count(), antes)

	def test_mass_assignment_aprovasaun_la_bele_forsa(self):
		self.client.force_login(self.users[roles.SEKRETARIA])
		self.client.post(reverse('membro-add'), {
			'nome': 'Hacker Teste', 'sex': 'Mane', 'date_of_birth': '1990-01-01', 'nu_eleitoral': 'e-1234', 'status': 'Ativu',
			'municipality': self.mun1.pk, 'post': self.post1.pk, 'village': self.vil1.pk, 'aldeia': self.ald1.pk,
			'aprovasaun': 'Aprovadu', 'aprovadu_husi': self.users[roles.PRESIDENTE].pk, 'user': self.users[roles.PRESIDENTE].pk,
			'hashed': 'a' * 64, 'razaun_rejeita': 'x'})
		m = Membro.objects.get(nu_eleitoral='E-1234')
		self.assertEqual(m.aprovasaun, 'Pendente')
		self.assertIsNone(m.aprovadu_husi)
		self.assertEqual(m.user, self.users[roles.SEKRETARIA])
		self.assertNotEqual(m.hashed, 'a' * 64)

	def test_sesaun_troka_bainhira_login(self):
		c = Client()
		c.get(reverse('login'))
		antes = c.session.session_key
		c.post(reverse('login'), {'username': roles.PRESIDENTE, 'password': PASS})
		self.assertNotEqual(antes, c.session.session_key)

	def test_pájina_error_la_hatudu_detallu(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get('/membro/hashi-la-iha/')
		self.assertEqual(r.status_code, 404)
		self.assertNotContains(r, 'Traceback', status_code=404)


class CsvInjectionTests(BaseData):
	FORMULA = '=HYPERLINK("http://evil.example","klik")'

	def setUp(self):
		self.m1.nome = self.FORMULA
		self.m1.telefone = '+67077000000'
		self.m1.area_estudu = '@SUM(1+1)'
		self.m1.esperensia = '-2+3'
		self.m1.save()

	def semua(self, resp):
		for linha in resp.content.decode('utf-8').splitlines():
			for sel in re.findall(r'(?:^|,)("(?:[^"]|"")*"|[^,]*)', linha):
				v = sel.strip('"')
				self.assertFalse(v[:1] in '=+-@' and v != '' and not v.lstrip('+-').replace('.', '').isdigit() or v.startswith(('=HYPER', '@SUM')),
					f'kélula perigozu: {v!r}')

	def test_export_membru(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get(reverse('membro-list') + '?export=csv')
		txt = r.content.decode('utf-8')
		self.assertIn("'=HYPERLINK", txt)
		self.assertNotIn(',=HYPERLINK', txt)
		self.assertIn("'+67077000000", txt)

	def test_export_rekursu(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get(reverse('report-rekursu'), {'hotu': '1', 'export': 'csv'})
		txt = r.content.decode('utf-8')
		self.assertIn("'=HYPERLINK", txt)
		self.assertIn("'@SUM", txt)
		self.assertIn("'-2+3", txt)

	def test_export_kuota_no_prezensa(self):
		import datetime
		from django.utils import timezone
		from eventu.models import Eventu, Prezensa
		from kuota.models import Kuota
		Kuota.objects.create(membro=self.m1, tinan=datetime.date.today().year, montante=5, data_selu=datetime.date.today(), nota='=1+1')
		ev = Eventu.objects.create(titulu='=cmd|calc', data_hahu=timezone.now(), kria_husi=self.users[roles.PRESIDENTE])
		Prezensa.objects.create(eventu=ev, membro=self.m1, estadu='Prezente')
		self.client.force_login(self.users[roles.PRESIDENTE])
		k = self.client.get(reverse('kuota-list'), {'export': 'csv'}).content.decode('utf-8')
		self.assertIn("'=HYPERLINK", k)
		self.assertIn("'=1+1", k)
		p = self.client.get(reverse('prezensa-csv', args=[ev.pk])).content.decode('utf-8')
		self.assertIn("'=cmd|calc", p)
		self.assertIn("'=HYPERLINK", p)

	def test_helper(self):
		from config.utils import csv_aman
		self.assertEqual(csv_aman('=1'), "'=1")
		self.assertEqual(csv_aman('\tx'), "'\tx")
		self.assertEqual(csv_aman('Ana'), 'Ana')
		self.assertEqual(csv_aman(5), 5)
		self.assertEqual(csv_aman(''), '')
		self.assertIsNone(csv_aman(None))


class XssTests(BaseData):
	def setUp(self):
		import datetime
		from django.utils import timezone
		from anunsiu.models import Anunsiu
		from custom.models import Departamentu
		from eventu.models import Eventu
		from kuota.models import Kuota
		from membro.models import Alokasaun
		from notif.models import Notifikasaun
		Membro.objects.filter(pk=self.m1.pk).update(nome=XSS, address=XSS, area_estudu=XSS, esperensia=XSS, kontribuisaun=XSS, servisu_fatin=XSS,
			date_of_birth=timezone.localdate().replace(year=1990))
		self.org.name = XSS
		self.org.titulu, self.org.sede = XSS, XSS
		self.org.save()
		self.dep_org.name = XSS
		self.dep_org.save()
		Alokasaun.objects.create(membro=self.m1, nivel='Departamentu', pozisaun='Membru', departamentu=self.dep_org, data_hahu=datetime.date(2026, 1, 1))
		Anunsiu.objects.create(titulu=XSS, mensagem=XSS, kria_husi=self.users[roles.PRESIDENTE])
		ev = Eventu.objects.create(titulu=XSS, fatin=XSS, deskrisaun=XSS, data_hahu=timezone.now() + datetime.timedelta(days=1), kria_husi=self.users[roles.PRESIDENTE])
		self.ev = ev
		Kuota.objects.create(membro=self.m1, tinan=datetime.date.today().year, montante=1, data_selu=datetime.date.today(), nota=XSS)
		Notifikasaun.objects.create(user=self.users[roles.PRESIDENTE], mesaun=XSS, url='/')
		self.m1.historia.create(membro_nome=XSS, aksaun='Kria', detalhe=XSS)

	def test_la_iha_script_la_escape(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		paginas = [reverse('home'), reverse('membro-list'), reverse('membro-detail', args=[self.m1.hashed]), reverse('membro-kartaun', args=[self.m1.hashed]),
			reverse('struktura-painel'), reverse('struktura-list', args=['departamentu']), reverse('struktura-list', args=['organizasaun']),
			reverse('report-dash'), reverse('report-rekursu') + f'?orgaun={self.org.pk}&hotu=1', reverse('report-kualidade'), reverse('report-aniversariu') + '?dias=30',
			reverse('kuota-list'), reverse('kuota-rezumu'), reverse('eventu-list'), reverse('eventu-detail', args=[self.ev.pk]),
			reverse('prezensa-foti', args=[self.ev.pk]), reverse('anunsiu-list'), reverse('notif-list'), reverse('historia-list'), reverse('aprovasaun-list'),
			reverse('membro-list') + '?q=' + XSS, reverse('kuota-list') + '?q=' + XSS, reverse('membro-search') + '?q=script']
		for url in paginas:
			r = self.client.get(url)
			self.assertEqual(r.status_code, 200, url)
			html = r.content.decode('utf-8')
			self.assertNotIn('<script>alert(1)</script>', html, f'XSS iha {url}')

	def test_master_no_form_la_xss(self):
		self.client.force_login(self.users[roles.ADMIN])
		for url in (reverse('master-list', args=['organizasaun']), reverse('master-list', args=['departamentu']), reverse('master-update', args=['organizasaun', self.org.pk])):
			html = self.client.get(url).content.decode('utf-8')
			self.assertNotIn('<script>alert(1)</script>', html, url)

	def test_navbar_orgaun_la_xss(self):
		self.client.force_login(self.users[roles.PRES_ORG])
		self.assertNotIn('<script>alert(1)</script>', self.client.get(reverse('home')).content.decode('utf-8'))

	def test_mensajen_flash_escape(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.post(reverse('prezensa-rapidu', args=[self.ev.pk]), {'nu_eleitoral': XSS}, follow=True)
		self.assertNotIn('<script>alert(1)</script>', r.content.decode('utf-8'))
		self.assertIn('&lt;script&gt;', r.content.decode('utf-8'))


class FotuUploadTests(BaseData):
	@classmethod
	def setUpClass(cls):
		cls._priv = tempfile.mkdtemp()
		cls._pub = tempfile.mkdtemp()
		cls._override = override_settings(PRIVATE_MEDIA_ROOT=cls._priv, MEDIA_ROOT=cls._pub)
		cls._override.enable()
		super().setUpClass()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		cls._override.disable()
		shutil.rmtree(cls._priv, ignore_errors=True)
		shutil.rmtree(cls._pub, ignore_errors=True)

	def dados(self, **kw):
		d = {'nome': 'Ho Fotu', 'sex': 'Mane', 'date_of_birth': '1990-01-01', 'nu_eleitoral': 'e-4444', 'status': 'Ativu',
			'municipality': self.mun1.pk, 'post': self.post1.pk, 'village': self.vil1.pk, 'aldeia': self.ald1.pk}
		d.update(kw)
		return d

	def upload(self, conteudu, nama='fotu.png', tipu='image/png'):
		self.client.force_login(self.users[roles.SEKRETARIA])
		return self.client.post(reverse('membro-add'), self.dados(image=SimpleUploadedFile(nama, conteudu, content_type=tipu)))

	def test_fotu_loos_rai_iha_storage_privadu(self):
		r = self.upload(gambar_bytes())
		self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
		m = Membro.objects.get(nu_eleitoral='E-4444')
		self.assertTrue(m.image.path.startswith(self._priv))
		self.assertFalse(m.image.path.startswith(self._pub))
		self.assertTrue(re.match(r'^membro_foto/[0-9a-f]{32}\.png$', m.image.name))

	def test_fotu_hatudu_deit_ho_login_no_área(self):
		self.upload(gambar_bytes())
		m = Membro.objects.get(nu_eleitoral='E-4444')
		url = reverse('membro-fotu', args=[m.hashed])
		self.assertEqual(Client().get(url).status_code, 302)                      # anonimu -> login
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get(url)
		self.assertEqual(r.status_code, 200)
		self.assertEqual(r['Content-Type'], 'image/png')
		self.assertIn('private', r['Cache-Control'])
		self.assertEqual(self.client.get(reverse('membro-fotu', args=[self.m1.hashed])).status_code, 404)   # laiha fotu
		self.client.force_login(self.users[roles.KOORD_SUKU])                      # área sei diferente? m foun iha suku/aldeia hanesan
		self.assertEqual(self.client.get(url).status_code, 200)
		Membro.objects.filter(pk=m.pk).update(municipality=self.mun2, post=self.post2, village=self.vil2, aldeia=self.ald2)
		self.assertEqual(self.client.get(url).status_code, 404)                    # sai husi área
		self.client.force_login(self.users[roles.ADMIN])
		self.assertEqual(self.client.get(url).status_code, 403)

	def test_fotu_la_expoin_liu_media_url(self):
		self.upload(gambar_bytes())
		m = Membro.objects.get(nu_eleitoral='E-4444')
		self.client.force_login(self.users[roles.PRESIDENTE])
		html = self.client.get(reverse('membro-detail', args=[m.hashed])).content.decode('utf-8')
		self.assertIn(reverse('membro-fotu', args=[m.hashed]), html)
		self.assertNotIn('/media/', html.replace('/media/images', ''))
		self.assertEqual(self.client.get('/media/' + m.image.name).status_code, 404)

	def test_la_aseita_file_la_imajen(self):
		for nama, kont in (('x.png', b'<?php echo 1; ?>'), ('x.png', b'%PDF-1.4 fake'), ('x.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'), ('x.html', b'<html></html>')):
			r = self.upload(kont, nama)
			self.assertEqual(r.status_code, 200, nama)
			self.assertIn('image', r.context['form'].errors, nama)
		self.assertFalse(Membro.objects.filter(nu_eleitoral='E-4444').exists())

	def test_imajen_boot_liu(self):
		r = self.upload(gambar_bytes(9000, 10))                                    # sisi > 8000
		self.assertEqual(r.status_code, 200)
		self.assertIn('image', r.context['form'].errors)
		grande = io.BytesIO()
		Image.new('RGB', (200, 200), (255, 255, 255)).save(grande, 'PNG', pnginfo=None)
		r = self.upload(grande.getvalue() + b'0' * (2 * 1024 * 1024 + 10))         # > 2 MB
		self.assertEqual(r.status_code, 200)
		self.assertIn('image', r.context['form'].errors)

	def test_naran_file_la_fiar(self):
		r = self.upload(gambar_bytes(), nama='../../etc/passwd.png')
		self.assertEqual(r.status_code, 302)
		m = Membro.objects.get(nu_eleitoral='E-4444')
		self.assertNotIn('..', m.image.name)
		self.assertTrue(m.image.path.startswith(self._priv))

	def test_logo_orgaun_validasaun(self):
		self.client.force_login(self.users[roles.ADMIN])
		url = reverse('master-update', args=['organizasaun', self.org.pk])
		base = {'code': self.org.code, 'name': self.org.name, 'is_active': 'on', 'titulu': '', 'sede': ''}
		r = self.client.post(url, {**base, 'logo': SimpleUploadedFile('l.png', b'<script>', content_type='image/png')})
		self.assertEqual(r.status_code, 200)
		r = self.client.post(url, {**base, 'logo': SimpleUploadedFile('l.png', gambar_bytes(), content_type='image/png')})
		self.assertEqual(r.status_code, 302)
		self.org.refresh_from_db()
		self.assertTrue(self.org.logo.path.startswith(self._pub))                  # logo públiku, iha MEDIA


class RedirectSeguruTests(BaseData):
	def test_notif_open_redirect(self):
		from notif.models import Notifikasaun
		self.client.force_login(self.users[roles.PRESIDENTE])
		for url in ('//evil.example/x', 'https://evil.example', '/\\evil.example', 'javascript:alert(1)', ''):
			n = Notifikasaun.objects.create(user=self.users[roles.PRESIDENTE], mesaun='x', url=url)
			r = self.client.get(reverse('notif-loke', args=[n.pk]))
			self.assertEqual(r['Location'], reverse('notif-list'), url)
		n = Notifikasaun.objects.create(user=self.users[roles.PRESIDENTE], mesaun='x', url='/membro/')
		self.assertEqual(self.client.get(reverse('notif-loke', args=[n.pk]))['Location'], '/membro/')

	def test_notif_uzuariu_seluk_la_bele(self):
		from notif.models import Notifikasaun
		n = Notifikasaun.objects.create(user=self.users[roles.SEKRETARIA], mesaun='x', url='/')
		self.client.force_login(self.users[roles.PRESIDENTE])
		self.assertEqual(self.client.get(reverse('notif-loke', args=[n.pk])).status_code, 404)

	def test_login_next_la_bele_ba_host_seluk(self):
		c = Client()
		r = c.post(reverse('login') + '?next=https://evil.example/', {'username': roles.PRESIDENTE, 'password': PASS})
		self.assertEqual(r['Location'], '/')


class KonfigurasaunTests(BaseData):
	def jalan_settings(self, env):
		with mock.patch('dotenv.load_dotenv', lambda *a, **k: None), mock.patch.dict(os.environ, env, clear=True):
			return runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Core', 'settings.py'))

	def test_debug_defeitu_la_aktivu_no_xave_obrigatoriu(self):
		with self.assertRaises(RuntimeError):
			self.jalan_settings({})
		s = self.jalan_settings({'DJANGO_SECRET_KEY': 'k' * 50})
		self.assertFalse(s['DEBUG'])
		self.assertTrue(s['SESSION_COOKIE_SECURE'] and s['CSRF_COOKIE_SECURE'] and s['SECURE_SSL_REDIRECT'])
		self.assertGreaterEqual(s['SECURE_HSTS_SECONDS'], 31536000)

	def test_debug_eksplisitu_deit(self):
		s = self.jalan_settings({'DJANGO_DEBUG': 'True'})
		self.assertTrue(s['DEBUG'])
		self.assertEqual(self.jalan_settings({'DJANGO_DEBUG': 'true', 'DJANGO_SECRET_KEY': 'k'})['DEBUG'], False)   # estritu: 'True' deit

	def test_upload_limite_no_media_privadu(self):
		from django.conf import settings
		self.assertLessEqual(settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 2 * 1024 * 1024)
		self.assertNotEqual(settings.PRIVATE_MEDIA_ROOT, settings.MEDIA_ROOT)
		self.assertFalse(settings.PRIVATE_MEDIA_ROOT.startswith(settings.MEDIA_ROOT))

	def test_laiha_xave_iha_repo(self):
		raiz = os.path.dirname(os.path.dirname(__file__))
		padraun = re.compile(r'(?i)(secret|password|passwd|token|api[_-]?key)\s*=\s*[\'"][^\'"\s]{12,}[\'"]')
		sala = []
		for dirp, dirs, files in os.walk(raiz):
			dirs[:] = [d for d in dirs if d not in ('.git', 'venv', '.venv', '__pycache__', 'static', 'staticfiles', 'media', 'private_media', 'node_modules')]
			for f in files:
				if f.endswith(('.py', '.html', '.js', '.md', '.example')) and not f.startswith('tests'):
					p = os.path.join(dirp, f)
					for i, l in enumerate(open(p, encoding='utf-8', errors='ignore'), 1):
						if padraun.search(l) and 'dev-only' not in l and 'example' not in l.lower():
							sala.append(f'{p}:{i}: {l.strip()[:80]}')
		self.assertEqual(sala, [])
