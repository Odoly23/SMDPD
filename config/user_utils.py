from django.db.models import Q
from config import roles


def c_user_group(user):
	if not user.is_authenticated:
		return None
	group = user.groups.all()[:1]
	return group[0].name if group else None


def c_user_scope(user):
	from user.models import UserScope
	return UserScope.objects.filter(user=user).select_related(
		'municipality', 'post', 'village', 'aldeia', 'departamentu', 'organizasaun').first()


def membro_scope(user, qs=None):
	"""Queryset Membro ne'ebé user bele hare tuir nia peran no área."""
	from membro.models import Membro
	qs = Membro.objects.all() if qs is None else qs
	group = c_user_group(user)
	if group in roles.NASIONAL_ROLES:
		return qs
	scope = c_user_scope(user)
	if scope:
		if group in roles.DEP_ROLES and scope.departamentu_id:
			return qs.filter(alokasaun__nivel='Departamentu', alokasaun__ativu='Sim',
				alokasaun__departamentu_id=scope.departamentu_id).distinct()
		if group in roles.MUN_ROLES and scope.municipality_id:
			return qs.filter(municipality_id=scope.municipality_id)
		if group in roles.POSTU_ROLES and scope.post_id:
			return qs.filter(post_id=scope.post_id)
		if group in roles.SUKU_ROLES and scope.village_id:
			return qs.filter(village_id=scope.village_id)
		if group in roles.ALDEIA_ROLES and scope.aldeia_id:
			return qs.filter(aldeia_id=scope.aldeia_id)
		if group in roles.ORG_ROLES and scope.organizasaun_id:
			return qs.filter(organizasaun_id=scope.organizasaun_id)
	return qs.none()


def alokasaun_scope(user, qs=None):
	"""Queryset Alokasaun (pozisaun iha struktura) ne'ebé user bele hare."""
	from membro.models import Alokasaun
	qs = Alokasaun.objects.all() if qs is None else qs
	group = c_user_group(user)
	if group in roles.NASIONAL_ROLES:
		return qs
	scope = c_user_scope(user)
	if scope:
		if group in roles.DEP_ROLES and scope.departamentu_id:
			return qs.filter(nivel='Departamentu', departamentu_id=scope.departamentu_id)
		if group in roles.MUN_ROLES and scope.municipality_id:
			mun = scope.municipality_id
			return qs.filter(
				Q(nivel='Munisipiu', municipality_id=mun)
				| Q(nivel='Postu', post__municipality_id=mun)
				| Q(nivel='Suku', village__administrativepost__municipality_id=mun)
				| Q(nivel='Aldeia', aldeia__village__administrativepost__municipality_id=mun))
		if group in roles.POSTU_ROLES and scope.post_id:
			post = scope.post_id
			return qs.filter(
				Q(nivel='Postu', post_id=post)
				| Q(nivel='Suku', village__administrativepost_id=post)
				| Q(nivel='Aldeia', aldeia__village__administrativepost_id=post))
		if group in roles.SUKU_ROLES and scope.village_id:
			return qs.filter(
				Q(nivel='Suku', village_id=scope.village_id)
				| Q(nivel='Aldeia', aldeia__village_id=scope.village_id))
		if group in roles.ALDEIA_ROLES and scope.aldeia_id:
			return qs.filter(nivel='Aldeia', aldeia_id=scope.aldeia_id)
		if group in roles.ORG_ROLES and scope.organizasaun_id:
			return qs.filter(nivel='Organizasaun', organizasaun_id=scope.organizasaun_id)
	return qs.none()


def can_aloka(user, nivel=None, departamentu_id=None):
	"""Presidente/Sekretaria Nasionál aloka iha nivel hotu; Presidente Departamentu deit iha nia departamentu rasik."""
	group = c_user_group(user)
	if group in (roles.PRESIDENTE, roles.SEKRETARIA):
		return True
	if group == roles.PRES_DEP:
		scope = c_user_scope(user)
		return bool(scope and scope.departamentu_id and nivel == 'Departamentu' and departamentu_id == scope.departamentu_id)
	return False

