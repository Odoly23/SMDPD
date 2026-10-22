"""Konta login ba pozisaun ne'ebé bele login. Membru ordináriu la iha login.

Pozisaun ne'ebé bele login (nivel, pozisaun) -> peran. Konta ligadu ba membru liu husi `UserScope.membro`.
"""
import re
import secrets
from django.contrib.auth.models import Group, User
from config import roles
from user.models import UserScope

LOGIN_PERAN = {
	('Nasional', 'Presidente'): roles.PRESIDENTE,
	('Nasional', 'Sekretaria'): roles.SEKRETARIA,
	('Departamentu', 'Presidente Departamentu'): roles.PRES_DEP,
	('Departamentu', 'Koordenador'): roles.KOORD_DEP,
	('Munisipiu', 'Koordenador'): roles.KOORD_MUN,
	('Postu', 'Koordenador'): roles.KOORD_POSTU,
	('Suku', 'Koordenador'): roles.KOORD_SUKU,
	('Aldeia', 'Koordenador'): roles.KOORD_ALDEIA,
	('Organizasaun', 'Presidente'): roles.PRES_ORG,
	('Organizasaun', 'Vice 1'): roles.VICE_ORG,
	('Organizasaun', 'Vice 2'): roles.VICE_ORG,
	('Organizasaun', 'Vice 3'): roles.VICE_ORG,
	('Organizasaun', 'Vice 4'): roles.VICE_ORG,
	('Organizasaun', 'Vice 5'): roles.VICE_ORG,
	('Organizasaun', 'Vice 6'): roles.VICE_ORG,
	('Organizasaun', 'Vice 7'): roles.VICE_ORG,
	('Organizasaun', 'Vice 8'): roles.VICE_ORG,
	('Organizasaun', 'Sekretaria'): roles.SEKR_ORG,
	('Organizasaun', 'Koordenador'): roles.KOORD_ORG,
}
# Se membru iha pozisaun barak, peran ne'ebé aas liu mak uza
PRIORIDADE = [roles.PRESIDENTE, roles.SEKRETARIA, roles.PRES_ORG, roles.PRES_DEP, roles.SEKR_ORG, roles.VICE_ORG,
	roles.KOORD_ORG, roles.KOORD_DEP, roles.KOORD_MUN, roles.KOORD_POSTU, roles.KOORD_SUKU, roles.KOORD_ALDEIA]
SCOPE_FIELDS = ['departamentu', 'municipality', 'post', 'village', 'aldeia', 'organizasaun']


def peran_login(a):
	"""Peran login ba alokasaun ida (ka None se pozisaun ne'e la bele login)."""
	if a.ativu != 'Sim':
		return None
	if a.nivel == 'Organizasaun' and a.municipality_id:
		return None                 # filiál orgaun iha munisipiu la iha login
	return LOGIN_PERAN.get((a.nivel, a.pozisaun))


def scope_ba(a):
	"""Área (UserScope) ba alokasaun ida."""
	data = {k: None for k in SCOPE_FIELDS}
	if a.nivel == 'Departamentu':
		data['departamentu'] = a.departamentu
	elif a.nivel == 'Munisipiu':
		data['municipality'] = a.municipality
	elif a.nivel == 'Postu':
		data['post'] = a.post
	elif a.nivel == 'Suku':
		data['village'] = a.village
	elif a.nivel == 'Aldeia':
		data['aldeia'] = a.aldeia
	elif a.nivel == 'Organizasaun':
		data['organizasaun'] = a.organizasaun
	return data


def pode_kria_login(user, a):
	"""Se `user` bele kria/atualiza konta login ba alokasaun `a`."""
	from config.user_utils import c_user_group, c_user_scope
	peran = peran_login(a)
	if not peran:
		return False
	group = c_user_group(user)
	if peran in roles.NASIONAL_ROLES:
		return group == roles.PRESIDENTE           # Presidente deit bele kria konta nasionál
	if group in (roles.PRESIDENTE, roles.SEKRETARIA):
		return True
	scope = c_user_scope(user)
	if not scope:
		return False
	if group == roles.PRES_DEP:
		return bool(a.nivel == 'Departamentu' and a.departamentu_id == scope.departamentu_id and a.pozisaun != 'Presidente Departamentu')
	if group == roles.PRES_ORG and scope.organizasaun_id:
		doma = (a.nivel == 'Organizasaun' and a.organizasaun_id == scope.organizasaun_id) or \
			(a.nivel == 'Departamentu' and a.departamentu and a.departamentu.organizasaun_id == scope.organizasaun_id)
		return bool(doma and a.pozisaun != 'Presidente')
	return False


def _username(membro):
	base = re.sub(r'[^a-z0-9]+', '', (membro.nu_eleitoral or 'membru').lower()) or 'membru'
	nome, n = base, 1
	while User.objects.filter(username=nome).exists():
		n += 1
		nome = f'{base}{n}'
	return nome


def _melhor(membro):
	"""Alokasaun ativu ho peran login ne'ebé aas liu (ka None)."""
	if membro.status != 'Ativu' or membro.aprovasaun != 'Aprovadu':
		return None, None
	opsaun = [(peran_login(a), a) for a in membro.alokasaun.select_related(
		'departamentu__organizasaun', 'municipality', 'post', 'village', 'aldeia', 'organizasaun')]
	opsaun = [(p, a) for p, a in opsaun if p]
	if not opsaun:
		return None, None
	opsaun.sort(key=lambda x: PRIORIDADE.index(x[0]))
	return opsaun[0]


def kria_login(membro, a):
	"""Kria (ka reset) konta login ba membru husi alokasaun `a`. Return (user, password_foun)."""
	peran = peran_login(a)
	scope = UserScope.objects.filter(membro=membro).select_related('user').first()
	password = secrets.token_urlsafe(9)
	if scope:
		user = scope.user
	else:
		user = User(username=_username(membro))
	user.first_name = membro.nome[:150]
	user.is_active = True
	user.set_password(password)
	user.save()
	user.groups.set([Group.objects.get_or_create(name=peran)[0]])
	UserScope.objects.update_or_create(user=user, defaults={'membro': membro, **scope_ba(a)})
	return user, password


def sinkroniza_login(membro):
	"""Atualiza peran/área konta membru tuir pozisaun atuál. Se la iha pozisaun login ka membru la ativu: desativa konta."""
	scope = UserScope.objects.filter(membro=membro).select_related('user').first()
	if not scope:
		return None
	user = scope.user
	peran, a = _melhor(membro)
	if not peran:
		user.is_active = False
		user.save(update_fields=['is_active'])
		return user
	user.groups.set([Group.objects.get_or_create(name=peran)[0]])
	for k, v in scope_ba(a).items():
		setattr(scope, k, v)
	scope.save()
	if not user.is_active:
		user.is_active = True
		user.save(update_fields=['is_active'])
	return user


def desativa_login(membro):
	scope = UserScope.objects.filter(membro=membro).select_related('user').first()
	if scope:
		scope.user.is_active = False
		scope.user.save(update_fields=['is_active'])
