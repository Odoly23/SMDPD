"""Limita tentativa login sala: 5 dala iha 10 minutu ba kombinasaun username + IP (uza cache Django)."""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver

MAXIMU = 5
LAIRAN = 10 * 60


def xave(username, ip):
	return f'login_gagal:{(username or "").strip().lower()}:{ip or "-"}'


def ip_husi(request):
	return (request.META.get('REMOTE_ADDR') if request else None) or '-'


def bloku(username, request):
	return cache.get(xave(username, ip_husi(request)), 0) >= MAXIMU


@receiver(user_login_failed)
def _gagal(sender, credentials=None, request=None, **kw):
	k = xave((credentials or {}).get('username'), ip_husi(request))
	try:
		cache.incr(k)
	except ValueError:
		cache.set(k, 1, LAIRAN)


@receiver(user_logged_in)
def _susesu(sender, request=None, user=None, **kw):
	cache.delete(xave(getattr(user, 'username', ''), ip_husi(request)))
