from django.db.models import Q
from config import roles
from config.user_utils import c_user_group, c_user_scope, c_user_unit, membro_scope
from eventu.models import Eventu, SCOPE_FIELDS
from membro.models import Membro

EVENTU_ROLES = [roles.PRESIDENTE, roles.SEKRETARIA, roles.PRES_DEP, roles.KOORD_DEP, roles.KOORD_MUN, roles.KOORD_POSTU,
	roles.KOORD_SUKU, roles.KOORD_ALDEIA, roles.PRES_ORG, roles.SEKR_ORG, roles.KOORD_ORG]


def scope_ba_eventu(user):
	"""Área eventu = área uzuáriu ne'ebé kria (nasionál = hotu mamuk)."""
	group = c_user_group(user)
	if group in roles.NASIONAL_ROLES:
		return {}
	scope = c_user_scope(user)
	if not scope:
		return {}
	return {k: getattr(scope, k) for k in SCOPE_FIELDS if getattr(scope, f'{k}_id')}


def eventu_ba(user):
	"""Eventu ne'ebé user bele hare: eventu nasionál, ka eventu husi área/unidade rasik (inklui munisipiu husi área geográfika)."""
	group = c_user_group(user)
	qs = Eventu.objects.select_related('municipality', 'post', 'village', 'aldeia', 'organizasaun', 'departamentu', 'kria_husi')
	if group in roles.NASIONAL_ROLES or group == roles.ADMIN:
		return qs
	nasional = Q(**{f'{k}__isnull': True for k in SCOPE_FIELDS})
	q = nasional
	scope = c_user_scope(user)
	if scope:
		for k in SCOPE_FIELDS:
			if getattr(scope, f'{k}_id'):
				q |= Q(**{k: getattr(scope, k)})
	u = c_user_unit(user)
	if u['municipality']:
		q |= Q(municipality=u['municipality'])
	if u['organizasaun']:
		q |= Q(organizasaun=u['organizasaun'])
	return qs.filter(q)


def pool_membru(user, ev):
	"""Membru ne'ebé bele foti prezensa ba eventu ida: aprovadu + ativu, iha área eventu no iha área uzuáriu."""
	qs = membro_scope(user).filter(aprovasaun='Aprovadu', status='Ativu')
	if ev.departamentu_id:
		qs = qs.filter(alokasaun__departamentu_id=ev.departamentu_id, alokasaun__ativu='Sim')
	for k in ('organizasaun', 'aldeia', 'village', 'post', 'municipality'):
		v = getattr(ev, f'{k}_id')
		if v:
			qs = qs.filter(**{f'{k}_id': v})
	return qs.distinct()
