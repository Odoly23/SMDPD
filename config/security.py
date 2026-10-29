"""Seguransa login: lokdaun tentativa sala (database), log login no helper IP.

Lokdaun: 5 tentativa sala iha 10 minutu ba kombinasaun username + IP -> bloku 10 minutu.
Hotu rai iha database (la depende ba cache/prosesu ida) no hetan log ba auditoria.
"""
import ipaddress
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import transaction
from django.dispatch import receiver
from django.utils import timezone

MAXIMU = 5
LAIRAN = timedelta(minutes=10)


def _ip_loos(valor):
	try:
		ipaddress.ip_address(valor)
		return valor
	except ValueError:
		return None


def ip_husi(request):
	if not request:
		return None
	if getattr(settings, 'TRUST_PROXY', False):
		xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
		ip = _ip_loos(xff.split(',')[0].strip()) if xff else None
		if ip:
			return ip
	return _ip_loos(request.META.get('REMOTE_ADDR') or '')


def xave(username, ip):
	return f'{(username or "").strip().lower()[:150]}|{ip or "-"}'


def rai_log(request, username, hasil, user=None):
	from config.models import LoginLog
	LoginLog.objects.create(user=user, username=(username or '')[:150], ip=ip_husi(request) if ip_husi(request) else None,
		user_agent=((request.META.get('HTTP_USER_AGENT', '') if request else '') or '')[:200], hasil=hasil)


def bloku(username, request):
	from config.models import LoginTentativa
	t = LoginTentativa.objects.filter(xave=xave(username, ip_husi(request))).first()
	return bool(t and t.bloku_to and t.bloku_to > timezone.now())


def hatama_gagal(username, request):
	"""Soma tentativa sala; se to'o limite -> bloku. Return se agora bloku."""
	from config.models import LoginTentativa
	agora = timezone.now()
	with transaction.atomic():
		t, _ = LoginTentativa.objects.select_for_update().get_or_create(xave=xave(username, ip_husi(request)), defaults={'ikus': agora})
		if agora - t.ikus > LAIRAN or (t.bloku_to and t.bloku_to <= agora):
			t.gagal, t.bloku_to = 0, None
		t.gagal += 1
		t.ikus = agora
		if t.gagal >= MAXIMU:
			t.bloku_to = agora + LAIRAN
		t.save()
	return t.gagal >= MAXIMU


def hamoos_gagal(username, request):
	from config.models import LoginTentativa
	LoginTentativa.objects.filter(xave=xave(username, ip_husi(request))).delete()


@receiver(user_login_failed)
def _gagal(sender, credentials=None, request=None, **kw):
	username = (credentials or {}).get('username')
	hatama_gagal(username, request)
	rai_log(request, username, 'Sala')


@receiver(user_logged_in)
def _susesu(sender, request=None, user=None, **kw):
	hamoos_gagal(getattr(user, 'username', ''), request)
	rai_log(request, getattr(user, 'username', ''), 'Susesu', user=user)


@receiver(user_logged_out)
def _sai(sender, request=None, user=None, **kw):
	if user is not None:
		rai_log(request, user.username, 'Sai', user=user)
