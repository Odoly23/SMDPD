import time
from datetime import timedelta
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from config import roles, totp
from config.models import KodeRekupera, LoginLog, LoginTentativa, Totp
from config.security import ip_husi
from config.tests import BaseData
from user.models import UserScope

PASS = 'x-Senha-123'


def kode_sekarang(secret):
	"""Kódigu agora ne'ebé seidauk uza (naktrik molok step)."""
	return totp.kode_agora(secret)


class TotpTests(TestCase):
	SECRET = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'          # '12345678901234567890' (RFC 6238)

	def test_vetor_rfc6238(self):
		# RFC 6238 (SHA1): T=59 -> 94287082, T=1111111109 -> 07081804, T=2000000000 -> 69279037 (6 dígitu terakhir)
		self.assertEqual(totp.kode_agora(self.SECRET, 59), '287082')
		self.assertEqual(totp.kode_agora(self.SECRET, 1111111109), '081804')
		self.assertEqual(totp.kode_agora(self.SECRET, 2000000000), '279037')

	def test_verifika_janela_no_replay(self):
		t = 1111111109
		step = t // 30
		self.assertEqual(totp.verifika(self.SECRET, '081804', t=t), step)
		self.assertEqual(totp.verifika(self.SECRET, '081804', t=t + 30), step)      # janela ±1
		self.assertIsNone(totp.verifika(self.SECRET, '081804', t=t + 90))           # liu janela
		self.assertIsNone(totp.verifika(self.SECRET, '081804', ultimu_step=step, t=t))   # replay
		self.assertIsNone(totp.verifika(self.SECRET, '000000', t=t))
		for sala in ('', None, 'abcdef', '12345', '1234567'):
			self.assertIsNone(totp.verifika(self.SECRET, sala, t=t))

	def test_secret_no_uri(self):
		s = totp.gera_secret()
		self.assertEqual(len(s), 32)
		self.assertTrue(totp.uri(s, 'a b').startswith('otpauth://totp/'))
		self.assertEqual(totp.formata('ABCDEFGH'), 'ABCD EFGH')


class LoginAmanTests(BaseData):
	def login_post(self, username, password=PASS, client=None):
		return (client or self.client).post(reverse('login'), {'username': username, 'password': password})

	def aktiva_2fa(self, user):
		t = Totp.objects.create(user=user, secret=totp.gera_secret(), aktivu=True)
		return t

	# ───── log no lokdaun iha database ─────
	def test_log_susesu_sala_sai(self):
		self.login_post(roles.PRESIDENTE, 'sala')
		self.login_post(roles.PRESIDENTE)
		self.client.post(reverse('logout'))
		self.assertEqual(list(LoginLog.objects.order_by('id').values_list('hasil', flat=True)), ['Sala', 'Susesu', 'Sai'])
		l = LoginLog.objects.first()
		self.assertEqual((l.username, l.ip), (roles.PRESIDENTE, '127.0.0.1'))

	def test_lokdaun_rai_iha_database_no_log_bloku(self):
		for _ in range(5):
			self.login_post(roles.PRESIDENTE, 'sala')
		t = LoginTentativa.objects.get()
		self.assertEqual(t.gagal, 5)
		self.assertGreater(t.bloku_to, timezone.now())
		r = self.login_post(roles.PRESIDENTE)
		self.assertEqual(r.status_code, 429)
		self.assertTrue(LoginLog.objects.filter(hasil='Bloku').exists())

	def test_lokdaun_remata(self):
		for _ in range(5):
			self.login_post(roles.PRESIDENTE, 'sala')
		LoginTentativa.objects.update(bloku_to=timezone.now() - timedelta(seconds=1), ikus=timezone.now() - timedelta(minutes=11))
		self.assertEqual(self.login_post(roles.PRESIDENTE).status_code, 302)
		self.assertFalse(LoginTentativa.objects.exists())

	def test_lokdaun_ip_seluk_la_afeta(self):
		for _ in range(5):
			self.login_post(roles.PRESIDENTE, 'sala')
		outro = Client(REMOTE_ADDR='10.1.2.3')
		self.assertEqual(self.login_post(roles.PRESIDENTE, client=outro).status_code, 302)

	def test_ip_proxy(self):
		class R:
			META = {'REMOTE_ADDR': '10.0.0.1', 'HTTP_X_FORWARDED_FOR': '203.0.113.9, 10.0.0.1'}
		self.assertEqual(ip_husi(R), '10.0.0.1')                      # la fiar proxy
		with override_settings(TRUST_PROXY=True):
			self.assertEqual(ip_husi(R), '203.0.113.9')
			R.META['HTTP_X_FORWARDED_FOR'] = 'bukan-ip'
			self.assertEqual(ip_husi(R), '10.0.0.1')                  # IP la loos ignora

	# ───── 2FA ─────
	def test_setup_no_aktivasaun_2fa(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get(reverse('seguransa-2fa'))
		self.assertContains(r, 'entrada manu')
		t = Totp.objects.get(user=self.users[roles.PRESIDENTE])
		self.assertFalse(t.aktivu)
		self.assertContains(r, totp.formata(t.secret))
		r = self.client.post(reverse('seguransa-2fa'), {'asaun': 'aktiva', 'kode': '000000'}, follow=True)
		self.assertContains(r, 'Kódigu la loos')
		t.refresh_from_db()
		self.assertFalse(t.aktivu)
		r = self.client.post(reverse('seguransa-2fa'), {'asaun': 'aktiva', 'kode': kode_sekarang(t.secret)})
		self.assertEqual(r.status_code, 200)
		self.assertEqual(len(r.context['kodes']), 8)
		t.refresh_from_db()
		self.assertTrue(t.aktivu)
		self.assertEqual(KodeRekupera.objects.filter(user=self.users[roles.PRESIDENTE]).count(), 8)
		# lalos hatudu fali kódigu
		self.assertNotIn('kodes', self.client.get(reverse('seguransa-2fa')).context or {})

	def test_login_ho_2fa(self):
		t = self.aktiva_2fa(self.users[roles.SEKRETARIA])
		r = self.login_post(roles.SEKRETARIA)
		self.assertRedirects(r, reverse('login-2fa'), fetch_redirect_response=False)
		self.assertNotIn('_auth_user_id', self.client.session)                    # seidauk login
		self.assertEqual(self.client.get(reverse('membro-list')).status_code, 302)
		r = self.client.post(reverse('login-2fa'), {'kode': '000000'})
		self.assertContains(r, 'Kódigu la loos')
		self.assertNotIn('_auth_user_id', self.client.session)
		kode = kode_sekarang(t.secret)
		r = self.client.post(reverse('login-2fa'), {'kode': kode})
		self.assertEqual(r.status_code, 302)
		self.assertEqual(self.client.session['_auth_user_id'], str(self.users[roles.SEKRETARIA].pk))
		self.assertEqual(self.client.get(reverse('membro-list')).status_code, 200)
		self.assertTrue(LoginLog.objects.filter(hasil='2FA sala').exists())
		self.assertTrue(LoginLog.objects.filter(hasil='Susesu', user=self.users[roles.SEKRETARIA]).exists())

	def test_2fa_replay(self):
		t = self.aktiva_2fa(self.users[roles.SEKRETARIA])
		kode = kode_sekarang(t.secret)
		self.login_post(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('login-2fa'), {'kode': kode}).status_code, 302)
		self.client.post(reverse('logout'))
		self.login_post(roles.SEKRETARIA)
		r = self.client.post(reverse('login-2fa'), {'kode': kode})                 # kódigu hanesan uza fali
		self.assertContains(r, 'Kódigu la loos')

	def test_kodigu_rekuperasaun_uza_dala_ida(self):
		from main.seguransa import _kodes_foun
		self.aktiva_2fa(self.users[roles.SEKRETARIA])
		kodes = _kodes_foun(self.users[roles.SEKRETARIA])
		self.login_post(roles.SEKRETARIA)
		self.assertEqual(self.client.post(reverse('login-2fa'), {'kode': kodes[0].lower()}).status_code, 302)
		self.client.post(reverse('logout'))
		self.login_post(roles.SEKRETARIA)
		self.assertContains(self.client.post(reverse('login-2fa'), {'kode': kodes[0]}), 'Kódigu la loos')
		self.assertEqual(self.client.post(reverse('login-2fa'), {'kode': kodes[1]}).status_code, 302)

	def test_lokdaun_2fa(self):
		self.aktiva_2fa(self.users[roles.SEKRETARIA])
		self.login_post(roles.SEKRETARIA)
		for _ in range(5):
			self.client.post(reverse('login-2fa'), {'kode': '111111'})
		r = self.client.post(reverse('login-2fa'), {'kode': '111111'})
		self.assertEqual(r.status_code, 429)
		self.assertNotIn('_auth_user_id', self.client.session)

	def test_pre2fa_la_valido_sein_password_ka_remata(self):
		self.assertRedirects(self.client.get(reverse('login-2fa')), reverse('login'))
		self.aktiva_2fa(self.users[roles.SEKRETARIA])
		self.login_post(roles.SEKRETARIA)
		s = self.client.session
		s['pre2fa']['ts'] = time.time() - 1000
		s.save()
		self.assertRedirects(self.client.get(reverse('login-2fa')), reverse('login'))
		self.assertNotIn('pre2fa', self.client.session)

	def test_2fa_la_bele_hasai_password_sala_ka_user_inativu(self):
		self.aktiva_2fa(self.users[roles.SEKRETARIA])
		self.login_post(roles.SEKRETARIA)
		User.objects.filter(pk=self.users[roles.SEKRETARIA].pk).update(is_active=False)
		self.assertRedirects(self.client.get(reverse('login-2fa')), reverse('login'))

	def test_login_next_seguru(self):
		u = self.users[roles.SEKRETARIA]
		t = self.aktiva_2fa(u)
		self.client.post(reverse('login') + '?next=//evil.example/x', {'username': u.username, 'password': PASS})
		r = self.client.post(reverse('login-2fa'), {'kode': kode_sekarang(t.secret)})
		self.assertEqual(r['Location'], '/')

	def test_desativa_2fa_presiza_password_no_kodigu(self):
		u = self.users[roles.PRESIDENTE]
		t = self.aktiva_2fa(u)
		self.client.force_login(u)
		self.client.post(reverse('seguransa-2fa'), {'asaun': 'desativa', 'password': 'sala', 'kode': kode_sekarang(t.secret)})
		self.assertTrue(Totp.objects.filter(user=u).exists())
		self.client.post(reverse('seguransa-2fa'), {'asaun': 'desativa', 'password': PASS, 'kode': '000000'})
		self.assertTrue(Totp.objects.filter(user=u).exists())
		self.client.post(reverse('seguransa-2fa'), {'asaun': 'desativa', 'password': PASS, 'kode': kode_sekarang(t.secret)})
		self.assertFalse(Totp.objects.filter(user=u).exists())

	@override_settings(SMDPD_2FA_WAJIBA=True)
	def test_2fa_obrigatoriu_ba_peran_sensitivu(self):
		for role in (roles.PRESIDENTE, roles.SEKRETARIA, roles.ADMIN):
			self.client.force_login(self.users[role])
			self.assertRedirects(self.client.get(reverse('home')), reverse('seguransa-2fa'), fetch_redirect_response=False)
			self.assertEqual(self.client.get(reverse('seguransa-2fa')).status_code, 200)       # pájina setup livre
			self.assertEqual(self.client.get(reverse('change-password')).status_code, 200)
		for role in (roles.KOORD_MUN, roles.PRES_ORG, roles.VICE_ORG):
			self.client.force_login(self.users[role])
			self.assertEqual(self.client.get(reverse('home')).status_code, 200, role)

	@override_settings(SMDPD_2FA_WAJIBA=True)
	def test_2fa_obrigatoriu_hotu_depois_aktiva(self):
		u = self.users[roles.PRESIDENTE]
		self.aktiva_2fa(u)
		self.client.force_login(u)
		self.assertEqual(self.client.get(reverse('home')).status_code, 200)
		t = Totp.objects.get(user=u)
		r = self.client.post(reverse('seguransa-2fa'), {'asaun': 'desativa', 'password': PASS, 'kode': kode_sekarang(t.secret)}, follow=True)
		self.assertContains(r, 'obrigatóriu')
		self.assertTrue(Totp.objects.filter(user=u).exists())

	# ───── sesaun ─────
	def test_sai_hotu(self):
		u = self.users[roles.SEKRETARIA]
		a, b = Client(), Client()
		self.login_post(u.username, client=a)
		self.login_post(u.username, client=b)
		self.assertEqual(a.get(reverse('home')).status_code, 200)
		self.assertEqual(b.get(reverse('home')).status_code, 200)
		self.assertEqual(a.post(reverse('sai-hotu')).status_code, 302)
		self.assertEqual(b.get(reverse('home')).status_code, 302)               # sesaun seluk mós sai
		self.assertEqual(a.get(reverse('home')).status_code, 302)
		other = Client()
		self.login_post(roles.PRESIDENTE, client=other)
		a2 = Client()
		self.login_post(u.username, client=a2)
		a2.post(reverse('sai-hotu'))
		self.assertEqual(other.get(reverse('home')).status_code, 200)           # uzuáriu seluk la afeta
		self.assertEqual(self.client.get(reverse('sai-hotu')).status_code, 302)  # tenke login

	def test_troka_password_hamoos_sesaun_seluk(self):
		u = self.users[roles.SEKRETARIA]
		a, b = Client(), Client()
		self.login_post(u.username, client=a)
		self.login_post(u.username, client=b)
		r = a.post(reverse('change-password'), {'old_password': PASS, 'new_password1': 'Troka-Foun-5555', 'new_password2': 'Troka-Foun-5555'})
		self.assertEqual(r.status_code, 302)
		self.assertEqual(a.get(reverse('home')).status_code, 200)
		self.assertEqual(b.get(reverse('home')).status_code, 302)

	def test_login_molok_ne_e(self):
		u = self.users[roles.SEKRETARIA]
		self.login_post(u.username)
		self.client.post(reverse('logout'))
		self.login_post(u.username)
		self.assertContains(self.client.get(reverse('home')), "Login molok ne'e")

	# ───── password no header ─────
	def test_password_minimu_10(self):
		for p in ('Abc12345', 'password12', '1234567890'):
			with self.assertRaises(ValidationError):
				password_validation.validate_password(p)
		password_validation.validate_password('Senha-Forte-987')

	def test_header_seguransa(self):
		self.client.force_login(self.users[roles.PRESIDENTE])
		r = self.client.get(reverse('home'))
		self.assertIn('no-store', r['Cache-Control'])
		self.assertIn('camera=()', r['Permissions-Policy'])
		self.assertEqual(r['X-Frame-Options'], 'DENY')
		self.assertEqual(r['X-Content-Type-Options'], 'nosniff')
		self.assertEqual(r['Referrer-Policy'], 'same-origin')
		self.assertIn('no-store', Client().get(reverse('login'))['Cache-Control'])

	def test_konfigurasaun_sesaun(self):
		from django.conf import settings
		self.assertTrue(settings.SESSION_COOKIE_HTTPONLY and settings.CSRF_COOKIE_HTTPONLY)
		self.assertEqual((settings.SESSION_COOKIE_SAMESITE, settings.CSRF_COOKIE_SAMESITE), ('Lax', 'Lax'))
		self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST and settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
		self.assertEqual(settings.SESSION_COOKIE_AGE, settings.SESSION_IDLE_MINUTES * 60)

	# ───── Admin ─────
	def test_admin_reset_password(self):
		alvu = self.users[roles.SEKRETARIA]
		sesaun = Client()
		self.login_post(alvu.username, client=sesaun)
		self.client.force_login(self.users[roles.ADMIN])
		r = self.client.post(reverse('user-reset', args=[alvu.pk]))
		self.assertEqual(r.status_code, 200)
		senha = r.context['password']
		self.assertGreaterEqual(len(senha), 10)
		self.assertEqual(self.login_post(alvu.username, PASS, client=Client()).status_code, 200)        # password antigu la valido
		novu = Client()
		self.assertEqual(self.login_post(alvu.username, senha, client=novu).status_code, 302)
		self.assertRedirects(novu.get(reverse('home')), reverse('change-password'), fetch_redirect_response=False)   # tenke troka
		self.assertEqual(sesaun.get(reverse('home')).status_code, 302)                                # sesaun antigu sai
		self.assertTrue(LoginLog.objects.filter(hasil='Reset', username=alvu.username).exists())

	def test_admin_la_bele_reset_rasik_no_seluk_la_bele(self):
		self.client.force_login(self.users[roles.ADMIN])
		self.assertEqual(self.client.post(reverse('user-reset', args=[self.users[roles.ADMIN].pk])).status_code, 302)
		self.assertTrue(self.users[roles.ADMIN].check_password(PASS))
		self.client.force_login(self.users[roles.PRESIDENTE])
		for nome in ('user-reset', 'user-reset-2fa'):
			self.assertEqual(self.client.post(reverse(nome, args=[self.users[roles.SEKRETARIA].pk])).status_code, 403, nome)
		self.assertEqual(self.client.get(reverse('user-log')).status_code, 403)

	def test_admin_reset_2fa(self):
		alvu = self.users[roles.SEKRETARIA]
		self.aktiva_2fa(alvu)
		KodeRekupera.objects.create(user=alvu, hash='x')
		self.client.force_login(self.users[roles.ADMIN])
		self.assertContains(self.client.get(reverse('user-list')), 'Reset 2FA')
		self.client.post(reverse('user-reset-2fa', args=[alvu.pk]))
		self.assertFalse(Totp.objects.filter(user=alvu).exists())
		self.assertFalse(KodeRekupera.objects.filter(user=alvu).exists())
		self.assertEqual(self.login_post(alvu.username, client=Client()).status_code, 302)

	def test_admin_log_login(self):
		self.login_post(roles.PRESIDENTE, 'sala')
		self.client.force_login(self.users[roles.ADMIN])
		r = self.client.get(reverse('user-log'))
		self.assertContains(r, roles.PRESIDENTE)
		self.assertEqual(len(self.client.get(reverse('user-log'), {'hasil': 'Bloku'}).context['page']), 0)
		self.assertEqual(len(self.client.get(reverse('user-log'), {'hasil': 'Sala'}).context['page']), 1)
		self.assertEqual(len(self.client.get(reverse('user-log'), {'q': 'president'}).context['page']), 1)

	def test_url_admin_django_bele_muda(self):
		from django.conf import settings
		self.assertTrue(settings.ADMIN_URL.endswith('/'))
