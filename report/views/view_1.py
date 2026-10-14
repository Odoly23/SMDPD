from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group, membro_scope, alokasaun_scope


def _rows(qs, id_field, name_field):
	"""Relatoriu total membru per unidade nu'udar lista {id, name, total}."""
	rows = qs.values(id_field, name_field).annotate(total=Count('id', distinct=True)).order_by(name_field)
	return [{'id': r[id_field], 'name': r[name_field], 'total': r['total']} for r in rows]


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
		'por_org': _rows(qs.filter(organizasaun__isnull=False), 'organizasaun_id', 'organizasaun__code'),
		'por_status': _rows(qs, 'status', 'status'),
		'por_tinan': _rows(qs.filter(data_hakbit__isnull=False), 'data_hakbit__year', 'data_hakbit__year'),
		'por_nivel': [{'name': n, 'total': struktura.filter(nivel=n).count()} for n in
			['Nasional', 'Departamentu', 'Munisipiu', 'Suku', 'Aldeia', 'Organizasaun']],
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
