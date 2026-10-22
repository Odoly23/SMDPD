"""2FA (TOTP), kódigu rekuperasaun no 'sai husi aparelhu hotu'."""
import secrets
import time
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from config import totp
from config.models import KodeRekupera, Totp
from config.security import bloku, hamoos_gagal, hatama_gagal, rai_log
from config.user_utils import c_user_group
from config.utils import hash_id

PRE2FA_VALIDU = 300       # segundu: tempu atu tau kódigu 2FA depois password loos
N_REKUPERA = 8


def _hash_kode(kode):
	return hash_id('rekupera:' + kode.strip().upper().replace('-', ''))


def _kodes_foun(user):
	"""Hamoos kódigu rekuperasaun antigu no kria foun (return lista testu klaru, hatudu dala ida deit)."""
	KodeRekupera.objects.filter(user=user).delete()
	kodes = []
	for _ in range(N_REKUPERA):
		k = secrets.token_hex(5).upper()
		kodes.append(f'{k[:5]}-{k[5:]}')
		KodeRekupera.objects.create(user=user, hash=_hash_kode(k))
	return kodes


def login_2fa(request):
	"""Pasu daruak login: kódigu 2FA (aplikasaun authenticator) ka kódigu rekuperasaun."""
	pre = request.session.get('pre2fa')
	if not pre or time.time() - pre.get('ts', 0) > PRE2FA_VALIDU:
		request.session.pop('pre2fa', None)
		messages.error(request, 'Sesaun login remata. Tama fali ho password.')
		return redirect('login')
	user = User.objects.filter(pk=pre['uid'], is_active=True).first()
	t = Totp.objects.filter(user=user, aktivu=True).first() if user else None
	if not (user and t):
		request.session.pop('pre2fa', None)
		return redirect('login')
	erru = None
	if request.method == 'POST':
		if bloku(user.username, request):
			rai_log(request, user.username, 'Bloku')
			erru = 'Tentativa sala barak liu. Hein minutu 10 no koko fali.'
			return render(request, 'home/login_2fa.html', {'erru': erru, 'username': user.username}, status=429)
		kode = (request.POST.get('kode') or '').strip()
		ok = False
		step = totp.verifika(t.secret, kode, t.ultimu_step)
		if step:
			t.ultimu_step = step
			t.save(update_fields=['ultimu_step'])
			ok = True
		else:
			rek = KodeRekupera.objects.filter(user=user, hash=_hash_kode(kode), usadu=False).first() if len(kode.replace('-', '')) == 10 else None
			if rek:
				rek.usadu = True
				rek.save(update_fields=['usadu'])
				ok = True
		if ok:
			destinu = pre.get('next') or '/'
			request.session.pop('pre2fa', None)
			hamoos_gagal(user.username, request)
			login(request, user, backend=pre['backend'])
			if not url_has_allowed_host_and_scheme(destinu, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
				destinu = '/'
			return redirect(destinu)
		hatama_gagal(user.username, request)
		rai_log(request, user.username, '2FA sala', user=user)
		erru = 'Kódigu la loos.'
	return render(request, 'home/login_2fa.html', {'erru': erru, 'username': user.username})


@login_required
def seguransa_2fa(request):
	"""Aktiva/hare estadu/desativa 2FA ba uzuáriu atuál."""
	user = request.user
	t = Totp.objects.filter(user=user).first()
	grupu = c_user_group(user)
	context = {'group': grupu, 'aktivu': bool(t and t.aktivu), 'title': 'Seguransa Konta (2FA)', 'legend': 'Seguransa Konta (2FA)',
		'n_rekupera': KodeRekupera.objects.filter(user=user, usadu=False).count()}
	if request.method == 'POST':
		asaun = request.POST.get('asaun')
		if asaun == 'aktiva' and t and not t.aktivu:
			step = totp.verifika(t.secret, request.POST.get('kode'))
			if step:
				t.aktivu, t.ultimu_step = True, step
				t.save()
				context.update({'aktivu': True, 'kodes': _kodes_foun(user), 'n_rekupera': N_REKUPERA})
				messages.success(request, '2FA aktiva ona. Rai kódigu rekuperasaun sira ne\'e iha fatin seguru.')
				return render(request, 'seguransa/2fa.html', context)
			messages.error(request, 'Kódigu la loos. Verifika relójiu telemovel no koko fali.')
		elif asaun in ('desativa', 'kodes') and t and t.aktivu:
			if not authenticate(request, username=user.username, password=request.POST.get('password', '')):
				messages.error(request, 'Password la loos.')
			elif not totp.verifika(t.secret, request.POST.get('kode'), t.ultimu_step):
				messages.error(request, 'Kódigu 2FA la loos.')
			elif asaun == 'desativa':
				if c_user_group(user) in ('admin', 'presidente', 'sekretaria') and getattr(__import__('django.conf', fromlist=['settings']).settings, 'SMDPD_2FA_WAJIBA', False):
					messages.error(request, 'Peran ida-ne\'e la bele desativa 2FA (obrigatóriu).')
				else:
					t.delete()
					KodeRekupera.objects.filter(user=user).delete()
					messages.warning(request, '2FA desativa ona.')
					return redirect('seguransa-2fa')
			else:
				context.update({'kodes': _kodes_foun(user), 'n_rekupera': N_REKUPERA})
				messages.success(request, 'Kódigu rekuperasaun foun kria ona. Kódigu antigu la valido tan.')
				return render(request, 'seguransa/2fa.html', context)
		return redirect('seguransa-2fa')
	if not (t and t.aktivu):
		if not t:
			t = Totp.objects.create(user=user, secret=totp.gera_secret())
		context.update({'secret': totp.formata(t.secret), 'uri': totp.uri(t.secret, user.username)})
	return render(request, 'seguransa/2fa.html', context)


@login_required
@require_POST
def sai_hotu(request):
	"""Sai husi aparelhu/browser hotu (hamoos sesaun hotu uzuáriu ne'e nian)."""
	uid = str(request.user.pk)
	n = 0
	for s in Session.objects.filter(expire_date__gte=timezone.now()):
		try:
			if s.get_decoded().get('_auth_user_id') == uid:
				s.delete()
				n += 1
		except Exception:
			continue
	rai_log(request, request.user.username, 'Sai hotu', user=request.user)
	logout(request)
	return redirect('login')
