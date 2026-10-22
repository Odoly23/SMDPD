import csv
import datetime
from decimal import Decimal
from config.utils import CsvAman
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group, membro_scope
from custom.models import Municipality, Organizasaun
from kuota.forms import KuotaForm
from kuota.models import Kuota
from membro.models import Membro
from membro.utils import log_historia

POR_HALAMAN = 30


def kuota_scope(user):
	return Kuota.objects.filter(membro__in=membro_scope(user))


def _tinan(request):
	t = request.GET.get('tinan', '')
	return int(t) if t.isdigit() and 2000 <= int(t) <= 2100 else datetime.date.today().year


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def KuotaList(request):
	group = c_user_group(request.user)
	tinan = _tinan(request)
	qs = kuota_scope(request.user).filter(tinan=tinan).select_related('membro', 'rejistu_husi')
	q = (request.GET.get('q') or '').strip()
	if q:
		qs = qs.filter(Q(membro__nome__icontains=q) | Q(membro__nu_eleitoral__icontains=q))
	if request.GET.get('export') == 'csv':
		response = HttpResponse(content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = f'attachment; filename="kuota_{tinan}.csv"'
		response.write('﻿')
		w = CsvAman(response)
		w.writerow(['Data Selu', 'Naran', 'Nu. Eleitoral', 'Tinan', 'Montante (USD)', 'Métodu', 'Nota'])
		for k in qs:
			w.writerow([k.data_selu, k.membro.nome, k.membro.nu_eleitoral or '', k.tinan, k.montante, k.metodu, k.nota])
		return response
	total = qs.aggregate(t=Sum('montante'), n=Count('membro', distinct=True))
	page = Paginator(qs, POR_HALAMAN).get_page(request.GET.get('page'))
	params = request.GET.copy()
	params.pop('page', None)
	context = {'group': group, 'page': page, 'tinan': tinan, 'q': q, 'qs': params.urlencode(), 'tinans': range(datetime.date.today().year + 1, 2019, -1),
		'total': total['t'] or Decimal('0'), 'n_membru': total['n'], 'can_add': group in roles.INPUT_ROLES, 'can_del': group in roles.INPUT_ROLES or group == roles.PRESIDENTE,
		'title': 'Kuota Membru', 'legend': 'Kuota Membru'}
	return render(request, 'kuota/list.html', context)


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def KuotaAdd(request):
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = KuotaForm(request.POST, user=request.user)
		if form.is_valid():
			k = form.save(commit=False)
			k.rejistu_husi = request.user
			k.save()
			log_historia(request.user, k.membro, 'Kuota', f'Kuota {k.tinan}: USD {k.montante} ({k.metodu})')
			messages.success(request, f'Kuota USD {k.montante} husi {k.membro.nome} rai ona.')
			return redirect(f"{reverse('kuota-list')}?tinan={k.tinan}")
	else:
		form = KuotaForm(user=request.user)
	context = {'form': form, 'group': group, 'cancel_url': '/kuota/', 'back_url': 'kuota-list', 'back_label': 'Kuota',
		'title': 'Rejistu Kuota', 'legend': 'Rejistu Kuota'}
	return render(request, 'kuota/form.html', context)


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES + [roles.PRESIDENTE])
@require_POST
def KuotaDel(request, pk):
	k = get_object_or_404(kuota_scope(request.user), pk=pk)
	if c_user_group(request.user) != roles.PRESIDENTE and k.rejistu_husi_id != request.user.pk:
		return render(request, 'home/403.html', status=403)
	log_historia(request.user, k.membro, 'Hamoos Kuota', f'Kuota {k.tinan}: USD {k.montante}')
	k.delete()
	messages.warning(request, 'Kuota hamoos ona.')
	return redirect('kuota-list')


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def KuotaSearch(request):
	q = (request.GET.get('q') or '').strip()
	objects = []
	if len(q) >= 2:
		objects = membro_scope(request.user).filter(aprovasaun='Aprovadu', status='Ativu').filter(
			Q(nome__icontains=q) | Q(nu_eleitoral__icontains=q))[:30]
	return render(request, 'membro/search_options.html', {'objects': objects})


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def KuotaRezumu(request):
	"""Rezumu kuota tinan ida: total, % membru ne'ebé selu, tuir munisipiu/orgaun no lista seidauk selu."""
	group = c_user_group(request.user)
	tinan = _tinan(request)
	membros = membro_scope(request.user).filter(aprovasaun='Aprovadu', status='Ativu')
	pagu = kuota_scope(request.user).filter(tinan=tinan)
	total = pagu.aggregate(t=Sum('montante'))['t'] or Decimal('0')
	selu_ids = set(pagu.values_list('membro_id', flat=True))
	n_ativu = membros.count()
	n_selu = len(selu_ids & set(membros.values_list('pk', flat=True)))
	por_mun = []
	for m in Municipality.objects.all():
		ativu = membros.filter(municipality=m).count()
		if not ativu:
			continue
		selu = pagu.filter(membro__municipality=m).aggregate(t=Sum('montante'), n=Count('membro', distinct=True))
		por_mun.append({'naran': m.name, 'ativu': ativu, 'selu': selu['n'], 'total': selu['t'] or Decimal('0'), 'pct': round(100 * selu['n'] / ativu)})
	por_org = []
	for o in Organizasaun.objects.filter(is_active=True):
		ativu = membros.filter(organizasaun=o).count()
		if not ativu:
			continue
		selu = pagu.filter(membro__organizasaun=o).aggregate(t=Sum('montante'), n=Count('membro', distinct=True))
		por_org.append({'naran': o.name, 'ativu': ativu, 'selu': selu['n'], 'total': selu['t'] or Decimal('0'), 'pct': round(100 * selu['n'] / ativu)})
	seidauk = membros.exclude(pk__in=selu_ids).order_by('nome')
	if request.GET.get('export') == 'csv':
		response = HttpResponse(content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = f'attachment; filename="kuota_seidauk_selu_{tinan}.csv"'
		response.write('﻿')
		w = CsvAman(response)
		w.writerow(['Naran', 'Nu. Eleitoral', 'Telemovel', 'Munisipiu', 'Orgaun/Movimentu'])
		for m in seidauk.select_related('municipality', 'organizasaun'):
			w.writerow([m.nome, m.nu_eleitoral or '', m.telefone or '', m.municipality or '', m.organizasaun or ''])
		return response
	page = Paginator(seidauk, POR_HALAMAN).get_page(request.GET.get('page'))
	context = {'group': group, 'tinan': tinan, 'tinans': range(datetime.date.today().year + 1, 2019, -1), 'total': total, 'n_ativu': n_ativu,
		'n_selu': n_selu, 'pct': round(100 * n_selu / n_ativu) if n_ativu else 0, 'por_mun': por_mun, 'por_org': por_org, 'page': page,
		'title': 'Rezumu Kuota', 'legend': 'Rezumu Kuota'}
	return render(request, 'kuota/rezumu.html', context)
