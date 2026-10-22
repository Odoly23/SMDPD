import csv
from config.utils import CsvAman
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group
from eventu.forms import EventuForm
from eventu.models import Eventu, Prezensa, ESTADU
from eventu.utils import EVENTU_ROLES, eventu_ba, pool_membru, scope_ba_eventu
from membro.utils import log_historia

LIAU = roles.VIEW_ROLES + [roles.ADMIN]
POR_HALAMAN = 40


def _hetan(request, pk):
	return get_object_or_404(eventu_ba(request.user), pk=pk)


def _bele_edita(user, ev):
	return c_user_group(user) == roles.PRESIDENTE or (ev.kria_husi_id == user.pk and c_user_group(user) in EVENTU_ROLES)


@login_required
@allowed_users(allowed_roles=LIAU)
def EventuList(request):
	group = c_user_group(request.user)
	agora = timezone.now()
	liu = request.GET.get('tab') == 'liu'
	qs = eventu_ba(request.user).annotate(
		n_prezente=Count('prezensa', filter=Q(prezensa__estadu='Prezente'), distinct=True))
	qs = qs.filter(data_hahu__lt=agora).order_by('-data_hahu') if liu else qs.filter(data_hahu__gte=agora).order_by('data_hahu')
	context = {'group': group, 'objects': qs[:200], 'liu': liu, 'can_add': group in EVENTU_ROLES, 'title': 'Eventu', 'legend': 'Eventu'}
	return render(request, 'eventu/list.html', context)


@login_required
@allowed_users(allowed_roles=EVENTU_ROLES)
def EventuAdd(request):
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = EventuForm(request.POST)
		if form.is_valid():
			ev = form.save(commit=False)
			ev.kria_husi = request.user
			for k, v in scope_ba_eventu(request.user).items():
				setattr(ev, k, v)
			ev.save()
			messages.success(request, 'Eventu kria ona.')
			return redirect('eventu-detail', ev.pk)
	else:
		form = EventuForm()
	context = {'form': form, 'group': group, 'cancel_url': '/eventu/', 'back_url': 'eventu-list', 'back_label': 'Eventu',
		'title': 'Eventu Foun', 'legend': 'Eventu Foun'}
	return render(request, 'main/form.html', context)


@login_required
@allowed_users(allowed_roles=EVENTU_ROLES)
def EventuUpdate(request, pk):
	group = c_user_group(request.user)
	ev = _hetan(request, pk)
	if not _bele_edita(request.user, ev):
		return render(request, 'home/403.html', status=403)
	if request.method == 'POST':
		form = EventuForm(request.POST, instance=ev)
		if form.is_valid():
			form.save()
			messages.success(request, 'Eventu atualiza ona.')
			return redirect('eventu-detail', ev.pk)
	else:
		form = EventuForm(instance=ev)
	context = {'form': form, 'group': group, 'cancel_url': f'/eventu/{ev.pk}/', 'back_url': 'eventu-list', 'back_label': 'Eventu',
		'title': 'Edita Eventu', 'legend': 'Edita Eventu'}
	return render(request, 'main/form.html', context)


@login_required
@allowed_users(allowed_roles=EVENTU_ROLES)
@require_POST
def EventuDel(request, pk):
	ev = _hetan(request, pk)
	if not _bele_edita(request.user, ev):
		return render(request, 'home/403.html', status=403)
	ev.delete()
	messages.warning(request, 'Eventu hamoos ona.')
	return redirect('eventu-list')


@login_required
@allowed_users(allowed_roles=LIAU)
def EventuDetail(request, pk):
	group = c_user_group(request.user)
	ev = _hetan(request, pk)
	total = {e: 0 for e, _ in ESTADU}
	for r in ev.prezensa.values('estadu').annotate(n=Count('id')):
		total[r['estadu']] = r['n']
	context = {
		'group': group, 'ev': ev, 'total': total, 'sub_total': sum(total.values()),
		'prezensas': ev.prezensa.select_related('membro').order_by('estadu', 'membro__nome')[:500],
		'can_manage': group in EVENTU_ROLES, 'can_edit': _bele_edita(request.user, ev),
		'title': ev.titulu, 'legend': ev.titulu
	}
	return render(request, 'eventu/detail.html', context)


@login_required
@allowed_users(allowed_roles=EVENTU_ROLES)
def PrezensaFoti(request, pk):
	"""Foti prezensa: lista membru (ho buka + paginasaun) ho botaun Prezente/Lisensa/Falta; POST rai ba membru iha pájina."""
	group = c_user_group(request.user)
	ev = _hetan(request, pk)
	pool = pool_membru(request.user, ev)
	if request.method == 'POST':
		ids = [int(i) for i in request.POST.getlist('membro_id') if i.isdigit()]
		valid = {m.pk for m in pool.filter(pk__in=ids)}
		sai = {e for e, _ in ESTADU}
		tot = 0
		for mid in ids:
			if mid not in valid:
				continue
			est = request.POST.get(f'estadu_{mid}', '')
			if est in sai:
				Prezensa.objects.update_or_create(eventu=ev, membro_id=mid, defaults={'estadu': est, 'rejistu_husi': request.user})
				tot += 1
			elif est == '-':
				Prezensa.objects.filter(eventu=ev, membro_id=mid).delete()
		messages.success(request, f'Prezensa rai ona ba {tot} membru.')
		return redirect(request.get_full_path())
	q = (request.GET.get('q') or '').strip()
	if q:
		pool = pool.filter(Q(nome__icontains=q) | Q(nu_eleitoral__icontains=q))
	hira = request.GET.get('hira')
	reg = {p.membro_id: p.estadu for p in ev.prezensa.all()}
	if hira == 'seidauk':
		pool = pool.exclude(pk__in=reg.keys())
	page = Paginator(pool.order_by('nome'), POR_HALAMAN).get_page(request.GET.get('page'))
	for m in page:
		m.estadu_atual = reg.get(m.pk, '')
	params = request.GET.copy()
	params.pop('page', None)
	context = {'group': group, 'ev': ev, 'page': page, 'q': q, 'hira': hira, 'qs': params.urlencode(), 'estadu': ESTADU,
		'title': 'Foti Prezensa', 'legend': 'Foti Prezensa'}
	return render(request, 'eventu/prezensa.html', context)


@login_required
@allowed_users(allowed_roles=EVENTU_ROLES)
@require_POST
def PrezensaRapidu(request, pk):
	"""Prezensa rápidu: hakerek nu. eleitoral -> Prezente."""
	ev = _hetan(request, pk)
	ele = (request.POST.get('nu_eleitoral') or '').strip().upper()
	m = pool_membru(request.user, ev).filter(nu_eleitoral__iexact=ele).first() if ele else None
	if not m:
		messages.error(request, f'Membru ho nu. eleitoral "{ele}" la hetan iha lista eventu ne\'e (tenke aprovadu, ativu no iha área).')
	else:
		_, foun = Prezensa.objects.update_or_create(eventu=ev, membro=m, defaults={'estadu': 'Prezente', 'rejistu_husi': request.user})
		messages.success(request, f'{m.nome} prezente.')
	return redirect('prezensa-foti', ev.pk)


@login_required
@allowed_users(allowed_roles=LIAU)
def PrezensaCsv(request, pk):
	ev = _hetan(request, pk)
	response = HttpResponse(content_type='text/csv; charset=utf-8')
	response['Content-Disposition'] = f'attachment; filename="prezensa_{ev.pk}.csv"'
	response.write('﻿')
	w = CsvAman(response)
	w.writerow([ev.titulu, ev.data_hahu.strftime('%d/%m/%Y %H:%M'), ev.fatin])
	w.writerow(['Nu.', 'Naran', 'Nu. Eleitoral', 'Estadu', 'Nota'])
	for i, p in enumerate(ev.prezensa.select_related('membro').order_by('membro__nome'), start=1):
		w.writerow([i, p.membro.nome, p.membro.nu_eleitoral or '', p.estadu, p.nota])
	return response
