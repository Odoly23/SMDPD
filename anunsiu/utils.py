from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from config import roles
from config.user_utils import c_user_group, c_user_unit
from notif.utils import kria_notif
from anunsiu.models import Anunsiu


def anunsiu_ba(user):
	"""Anunsiu ativu ne'ebé user bele hare (tuir peran no unidade)."""
	hoje = timezone.localdate()
	qs = Anunsiu.objects.filter(Q(data_remata__isnull=True) | Q(data_remata__gte=hoje))
	group = c_user_group(user)
	if group in roles.NASIONAL_ROLES or group == roles.ADMIN:
		return qs
	u = c_user_unit(user)
	q = Q(audiens='Hotu')
	if u['municipality']:
		q |= Q(audiens='Munisipiu', municipality=u['municipality'])
	if u['organizasaun']:
		q |= Q(audiens='Organizasaun', organizasaun=u['organizasaun'])
	if u['departamentu']:
		q |= Q(audiens='Departamentu', departamentu=u['departamentu'])
	return qs.filter(q)


def simu_anunsiu(a):
	"""Uzuáriu ativu ne'ebé tama iha audiens anunsiu (laiha ho kria_husi)."""
	from user.models import UserScope
	view = User.objects.filter(is_active=True, groups__name__in=roles.VIEW_ROLES)
	if a.audiens == 'Hotu':
		return view.exclude(pk=a.kria_husi_id)
	q = Q()
	if a.audiens == 'Munisipiu':
		m = a.municipality_id
		q = Q(scope__municipality_id=m) | Q(scope__post__municipality_id=m) | Q(scope__village__administrativepost__municipality_id=m) \
			| Q(scope__aldeia__village__administrativepost__municipality_id=m)
	elif a.audiens == 'Organizasaun':
		q = Q(scope__organizasaun_id=a.organizasaun_id) | Q(scope__departamentu__organizasaun_id=a.organizasaun_id)
	elif a.audiens == 'Departamentu':
		q = Q(scope__departamentu_id=a.departamentu_id)
	nasional = Q(groups__name__in=roles.NASIONAL_ROLES)
	return view.filter(q | nasional).exclude(pk=a.kria_husi_id).distinct()


def notifika(a):
	kria_notif(list(simu_anunsiu(a)), f'Anunsiu: {a.titulu}', '/anunsiu/')
