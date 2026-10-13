from django.contrib.auth.models import User
from config import roles
from notif.models import Notifikasaun


def kria_notif(users, mesaun, url=''):
	"""Kria notifikasaun ba user (ka lista user) sira."""
	if isinstance(users, User):
		users = [users]
	Notifikasaun.objects.bulk_create([Notifikasaun(user=u, mesaun=mesaun, url=url) for u in users if u])


def notif_aprovador(mesaun, url=''):
	"""Notifika Presidente Nasionál sira ne'ebé ativu."""
	kria_notif(User.objects.filter(is_active=True, groups__name__in=roles.APROVA_ROLES), mesaun, url)
