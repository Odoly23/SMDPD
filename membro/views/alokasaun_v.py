from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group, alokasaun_scope, can_aloka, membro_scope
from custom.models import Organizasaun
from membro.forms import AlokasaunForm
from membro.models import Alokasaun, NIVEL, NIVEL_SLUG
from membro.utils import log_historia


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def StrukturaPainel(request):
	"""Painel Struktura PLP: total membru ba entidade (Orgaun/Movimentu no Struktura) no ba nivel struktura."""
	group = c_user_group(request.user)
	membros = membro_scope(request.user)
	aloks = alokasaun_scope(request.user).filter(ativu='Sim')
	total_org = membros.filter(organizasaun__isnull=False).distinct().count()
	total_str = aloks.exclude(nivel='Organizasaun').values('membro_id').distinct().count()
	por_org = {r['organizasaun_id']: r['n'] for r in membros.filter(organizasaun__isnull=False).order_by().values('organizasaun_id').annotate(n=Count('id', distinct=True))}
	orgaun = [{'obj': o, 'total': por_org.get(o.pk, 0)} for o in Organizasaun.objects.filter(is_active=True)]
	por_nivel = {r['nivel']: r['n'] for r in aloks.order_by().values('nivel').annotate(n=Count('membro_id', distinct=True))}
	struktura = [{'slug': n.lower(), 'name': label, 'total': por_nivel.get(n, 0)} for n, label in NIVEL if n != 'Organizasaun']
	page = Paginator(orgaun, 10).get_page(request.GET.get('page'))
	context = {
		'group': group, 'page': page, 'struktura': struktura, 'total_org': total_org, 'total_str': total_str,
		'total_orgaun': sum(r['total'] for r in page.paginator.object_list), 'total_struktura': total_str,
		'total_entidade': total_org + total_str, 'total_membru': membros.count(),
		'can_add': group in roles.INPUT_ROLES,
		'title': 'Painel Struktura', 'legend': 'Painel Struktura'
	}
	return render(request, 'membro/struktura_painel.html', context)


def _label(alokasaun):
	return f'{alokasaun.pozisaun} {alokasaun.nivel} {alokasaun.unit() or ""}'.strip()


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def StrukturaList(request, nivel):
	"""Lista pozisaun iha struktura ida (Nasionál, Departamentu, Munisipiu, Suku, Aldeia, Organizasaun)."""
	if nivel not in NIVEL_SLUG:
		raise Http404
	nama = NIVEL_SLUG[nivel]
	group = c_user_group(request.user)
	objects = sorted(
		alokasaun_scope(request.user).filter(nivel=nama).select_related(
			'membro', 'departamentu', 'municipality', 'village', 'aldeia', 'organizasaun'),
		key=lambda a: (a.ativu != 'Sim', str(a.unit() or ''), a.rank()))
	label = dict(NIVEL)[nama]
	context = {
		'group': group, 'objects': objects, 'nivel': nivel, 'nivel_label': label, 'can_aloka': group in roles.ALOKA_ROLES,
		'title': f'Struktura {label}', 'legend': f'Struktura {label}'
	}
	return render(request, 'membro/alokasaun_list.html', context)


def _form_context(form, group, nivel, legend):
	return {
		'form': form, 'group': group, 'cancel_url': f'/membro/struktura/{nivel}/',
		'back_url': 'struktura-list', 'back_args': [nivel], 'back_label': 'Struktura',
		'title': legend, 'legend': legend
	}


@login_required
@allowed_users(allowed_roles=roles.ALOKA_ROLES)
def AlokasaunAdd(request):
	group = c_user_group(request.user)
	nivel = (request.GET.get('nivel') or 'nasional').lower()
	if nivel not in NIVEL_SLUG:
		nivel = 'nasional'
	if request.method == 'POST':
		form = AlokasaunForm(request.POST, user=request.user)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.datetime = timezone.now()
			instance.user = request.user
			instance.save()
			log_historia(request.user, instance.membro, 'Aloka', _label(instance))
			messages.success(request, 'Pozisaun aloka ona.')
			return redirect('struktura-list', instance.nivel.lower())
	else:
		form = AlokasaunForm(user=request.user, initial={'nivel': NIVEL_SLUG[nivel]})
	return render(request, 'membro/alokasaun_form.html', _form_context(form, group, nivel, 'Aloka Pozisaun'))


@login_required
@allowed_users(allowed_roles=roles.ALOKA_ROLES)
def AlokasaunUpdate(request, pk):
	group = c_user_group(request.user)
	obj = get_object_or_404(Alokasaun, pk=pk)
	if not can_aloka(request.user, obj.nivel, obj.departamentu_id):
		return render(request, 'home/403.html', status=403)
	if request.method == 'POST':
		form = AlokasaunForm(request.POST, instance=obj, user=request.user)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.datetime = timezone.now()
			instance.user = request.user
			instance.save()
			log_historia(request.user, instance.membro, 'Edita Pozisaun', f'{_label(instance)}, ativu: {instance.ativu}')
			messages.success(request, 'Pozisaun atualiza ona.')
			return redirect('struktura-list', instance.nivel.lower())
	else:
		form = AlokasaunForm(instance=obj, user=request.user)
	return render(request, 'membro/alokasaun_form.html', _form_context(form, group, obj.nivel.lower(), 'Edita Pozisaun'))


@login_required
@allowed_users(allowed_roles=roles.ALOKA_ROLES)
@require_POST
def AlokasaunDel(request, pk):
	obj = get_object_or_404(Alokasaun, pk=pk)
	if not can_aloka(request.user, obj.nivel, obj.departamentu_id):
		return render(request, 'home/403.html', status=403)
	nivel = obj.nivel.lower()
	log_historia(request.user, obj.membro, 'Hamoos Pozisaun', _label(obj))
	obj.delete()
	messages.warning(request, 'Hamoos ho Susesu!.')
	return redirect('struktura-list', nivel)
