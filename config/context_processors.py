from django.urls import reverse
from config import roles
from config.user_utils import c_user_group

ROLE_NAME = dict(roles.ROLE_LABELS)

STRUKTURA = [
	('nasional', 'Nasionál', 'fa-flag'),
	('departamentu', 'Departamentu', 'fa-briefcase'),
	('munisipiu', 'Munisipiu', 'fa-building'),
	('suku', 'Suku', 'fa-map-marker'),
	('aldeia', 'Aldeia', 'fa-home'),
	('organizasaun', 'Organizasaun', 'fa-users'),
]
MASTER = [
	('munisipiu', 'Munisipiu', 'fa-building'),
	('postu', 'Postu', 'fa-map-signs'),
	('suku', 'Suku', 'fa-map-marker'),
	('aldeia', 'Aldeia', 'fa-map-o'),
	('departamentu', 'Departamentu', 'fa-briefcase'),
	('organizasaun', 'Organizasaun', 'fa-flag'),
]


def _item(request, label, icon, name, args=(), names=(), match_kwargs=None):
	"""Entrada menu ida. Ativu se url_name atuál inklui iha `names` (no kwargs hanesan)."""
	url = reverse(name, args=args)
	match = request.resolver_match
	active = bool(match) and (match.url_name in (names or (name,)))
	if active and match_kwargs:
		active = all(str(match.kwargs.get(k)) == str(v) for k, v in match_kwargs.items())
	return {'label': label, 'icon': icon, 'url': url, 'active': active, 'children': []}


def _grupu(request, label, icon, children):
	return {'label': label, 'icon': icon, 'url': '#', 'active': any(c['active'] for c in children), 'children': children}


def _menu(request, group):
	items = [_item(request, 'Varanda', 'fa-home', 'home')]
	if group == roles.ADMIN:
		items.append(_item(request, 'Uzuáriu', 'fa-user-circle', 'user-list', names=('user-list', 'user-add', 'user-update')))
		items.append(_grupu(request, 'Data Master', 'fa-database', [
			_item(request, label, icon, 'master-list', args=(tipu,), names=('master-list', 'master-add', 'master-update'),
				match_kwargs={'tipu': tipu}) for tipu, label, icon in MASTER]))
		items.append(_item(request, 'Historia', 'fa-history', 'historia-list'))
		return items
	if group in roles.VIEW_ROLES:
		items.append(_item(request, 'Membru', 'fa-list', 'membro-list', names=('membro-list', 'membro-detail', 'membro-update')))
		if group in roles.INPUT_ROLES:
			items.append(_item(request, 'Aumenta Membru', 'fa-plus', 'membro-add'))
		if group in roles.APROVA_ROLES:
			items.append(_item(request, 'Aprovasaun', 'fa-check-square-o', 'aprovasaun-list', names=('aprovasaun-list', 'aprovasaun-rejeita')))
		items.append(_grupu(request, 'Struktura', 'fa-sitemap', [
			_item(request, label, icon, 'struktura-list', args=(slug,), names=('struktura-list', 'alokasaun-add', 'alokasaun-update'),
				match_kwargs={'nivel': slug} if slug else None) for slug, label, icon in STRUKTURA]))
		items.append(_item(request, 'Relatoriu', 'fa-table', 'report-dash'))
		items.append(_item(request, 'Grafik', 'fa-bar-chart', 'report-chart'))
		if group in roles.HISTORIA_ROLES:
			items.append(_item(request, 'Historia', 'fa-history', 'historia-list'))
	return items


def nav_context(request):
	context = {'nav_items': [], 'nav_role': '', 'notif_total': 0, 'notif_recent': []}
	if request.user.is_authenticated:
		from notif.models import Notifikasaun
		group = c_user_group(request.user)
		context['nav_role'] = ROLE_NAME.get(group, '')
		context['nav_items'] = _menu(request, group)
		unread = Notifikasaun.objects.filter(user=request.user, is_read=False)
		context['notif_total'] = unread.count()
		context['notif_recent'] = list(unread[:5])
	return context
