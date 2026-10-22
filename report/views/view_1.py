from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from config import roles
from config.decorators import allowed_users
from membro.models import NIVEL
from config.user_utils import c_user_group, membro_scope, alokasaun_scope


def _rows(qs, id_field, name_field):
	"""Relatoriu total membru per unidade nu'udar lista {id, name, total}."""
	rows = qs.values(id_field, name_field).annotate(total=Count('id', distinct=True)).order_by(name_field)
	return [{'id': r[id_field], 'name': r[name_field] if r[name_field] is not None else 'Laiha', 'total': r['total']} for r in rows]


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def Dash(request):
	group = c_user_group(request.user)
	qs = membro_scope(request.user)
	tot = qs.aggregate(
		total=Count('id', distinct=True),
		mane=Count('id', filter=Q(sex='Mane'), distinct=True),
		feto=Count('id', filter=Q(sex='Feto'), distinct=True),
		pendente=Count('id', filter=Q(aprovasaun='Pendente'), distinct=True),
		aprovadu=Count('id', filter=Q(aprovasaun='Aprovadu'), distinct=True),
		rejeitadu=Count('id', filter=Q(aprovasaun='Rejeitadu'), distinct=True),
		sem_org=Count('id', filter=Q(organizasaun__isnull=True), distinct=True),
	)
	struktura = alokasaun_scope(request.user).filter(ativu='Sim').exclude(pozisaun='Membru')
	context = {
		'group': group, 'tot': tot,
		'por_munisipiu': _rows(qs, 'municipality_id', 'municipality__name'),
		'por_postu': _rows(qs, 'post_id', 'post__name'),
		'por_suku': _rows(qs, 'village_id', 'village__name'),
		'por_aldeia': _rows(qs, 'aldeia_id', 'aldeia__name'),
		'por_org': _rows(qs.filter(organizasaun__isnull=False), 'organizasaun_id', 'organizasaun__name'),
		'por_status': _rows(qs, 'status', 'status'),
		'por_tinan': _rows(qs.filter(data_hakbit__isnull=False), 'data_hakbit__year', 'data_hakbit__year'),
		'por_nivel': [{'slug': n.lower(), 'name': label, 'total': struktura.filter(nivel=n).count()} for n, label in NIVEL],
		'title': 'Relatoriu Membru', 'legend': 'Relatoriu Membru'
	}
	return render(request, 'report/dash.html', context)


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def ChartDash(request):
	context = {
		'group': c_user_group(request.user),
		'title': 'Grafik Membru', 'legend': 'Grafik Membru'
	}
	return render(request, 'report/chart_dash.html', context)


REKURSU_KOLUNA = ['No', 'Naran', 'Area Estudu', 'Nivel Estudu / Gelar', 'Deskrisaun konaba Esperensia Servisu',
	'Kontribuisaun ba Programa PLP', 'Munisipiu Orijin', 'Munisipiu Rezidensia', 'Nu. Kontaktu', 'Email']
REKURSU_LIMITE = 2000


def _org_ba(user, group):
	"""Orgaun/movimentu ne'ebé user ne'e fixa ba (peran orgaun ka departamentu husi orgaun) ka None (nasionál: hili)."""
	from config.user_utils import c_user_scope
	scope = c_user_scope(user)
	if not scope:
		return None
	if group in roles.ORG_ROLES:
		return scope.organizasaun
	if group in roles.DEP_ROLES and scope.departamentu_id:
		return scope.departamentu.organizasaun
	return None


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def Rekursu(request):
	"""Baze de Dadus ba Rekursu Intelektuais (formulariu Orgaun Konsultivu/SEE): lista tuir ordem alfabetiku, bele imprime no esporta CSV."""
	import csv
	from django.db.models import Q
	from django.db.models.functions import Lower
	from django.http import HttpResponse
	from custom.models import Organizasaun
	group = c_user_group(request.user)
	fixa = _org_ba(request.user, group)
	orgs = Organizasaun.objects.filter(is_active=True) if not fixa else Organizasaun.objects.filter(pk=fixa.pk)
	qs = membro_scope(request.user)
	org_id = str(fixa.pk) if fixa else request.GET.get('orgaun', '')
	org = orgs.filter(pk=org_id).first() if org_id.isdigit() else None
	if org:
		qs = qs.filter(organizasaun=org)
	hotu = request.GET.get('hotu') == '1'
	if not hotu:   # defeitu: deit ne'ebé iha dadus rekursu intelektual (área estudu ka nivel)
		qs = qs.filter(Q(area_estudu__gt='') | Q(nivel_edukasaun__gt=''))
	q = (request.GET.get('q') or '').strip()
	if q:
		qs = qs.filter(Q(nome__icontains=q) | Q(area_estudu__icontains=q) | Q(esperensia__icontains=q) | Q(kontribuisaun__icontains=q))
	qs = qs.select_related('municipality', 'municipality_orijin').order_by(Lower('nome')).distinct()
	if request.GET.get('export') == 'csv':
		response = HttpResponse(content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = 'attachment; filename="rekursu_intelektual.csv"'
		response.write('﻿')
		w = csv.writer(response)
		w.writerow(REKURSU_KOLUNA)
		for i, m in enumerate(qs[:REKURSU_LIMITE], start=1):
			w.writerow([i, m.nome, m.area_estudu or '', m.nivel_edukasaun or '', m.esperensia or '', m.kontribuisaun or '',
				m.municipality_orijin or '', m.municipality or '', m.telefone or '', m.email or ''])
		return response
	objects = list(qs[:REKURSU_LIMITE + 1])
	logo = org.logo.url if org and org.logo else None
	context = {
		'group': group, 'orgs': orgs, 'org': org, 'fixa': fixa, 'objects': objects[:REKURSU_LIMITE], 'lebih': len(objects) > REKURSU_LIMITE,
		'limite': REKURSU_LIMITE, 'hotu': hotu, 'q': q, 'logo': logo, 'koluna': REKURSU_KOLUNA,
		'title': 'Rekursu Intelektual', 'legend': 'Rekursu Intelektual'
	}
	return render(request, 'report/rekursu.html', context)
