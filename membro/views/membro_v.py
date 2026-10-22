from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group, c_user_scope, membro_scope
from custom.models import Municipality, Organizasaun
from membro.forms import MembroForm
from membro.models import Membro, Alokasaun
from membro.akun import sinkroniza_login, desativa_login
from membro.utils import snapshot, diff_snapshot, log_historia, apply_filters, export_csv
from notif.utils import notif_aprovador

POR_HALAMAN = 25


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def MembroList(request):
	group = c_user_group(request.user)
	objects = membro_scope(request.user).select_related('municipality', 'post', 'village', 'aldeia', 'organizasaun')
	objects = apply_filters(objects, request.GET)
	if request.GET.get('export') == 'csv':
		return export_csv(objects)
	page = Paginator(objects, POR_HALAMAN).get_page(request.GET.get('page'))
	params = request.GET.copy()
	params.pop('page', None)
	context = {
		'group': group, 'page': page, 'total': page.paginator.count, 'qs': params.urlencode(), 'f': request.GET,
		'municipios': Municipality.objects.all(), 'organizasauns': Organizasaun.objects.filter(is_active=True),
		'can_add': group in roles.INPUT_ROLES, 'can_aprova': group in roles.APROVA_ROLES,
		'title': 'Lista Membru', 'legend': 'Lista Membru'
	}
	return render(request, 'membro/list.html', context)


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def MembroDetail(request, hashid):
	group = c_user_group(request.user)
	obj = get_object_or_404(membro_scope(request.user), hashed=hashid)
	alokasauns = Alokasaun.objects.filter(membro=obj, ativu='Sim').select_related(
		'departamentu', 'municipality', 'village', 'aldeia', 'organizasaun')
	historias = obj.historia.select_related('user')[:50] if group in roles.HISTORIA_ROLES else None
	context = {
		'group': group, 'obj': obj, 'hashid': hashid, 'alokasauns': alokasauns, 'historias': historias,
		'prezensas': obj.prezensa.select_related('eventu').order_by('-eventu__data_hahu')[:10],
		'can_edit': group in roles.INPUT_ROLES,
		'can_aprova': group in roles.APROVA_ROLES and obj.aprovasaun == 'Pendente',
		'can_del': group in roles.APROVA_ROLES,
		'title': 'Detalha Membru', 'legend': 'Detalha Membru'
	}
	return render(request, 'membro/detail.html', context)


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def MembroAdd(request):
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = MembroForm(request.POST, request.FILES, user=request.user)
		if form.is_valid():
			instance = form.save(commit=False)
			instance.aprovasaun = 'Pendente'
			instance.datetime = timezone.now()
			instance.user = request.user
			instance.save()
			log_historia(request.user, instance, 'Kria', f'Membru foun: {instance}')
			notif_aprovador(f'Membru foun hein aprovasaun: {instance.nome}', f'/membro/{instance.hashed}/')
			messages.success(request, 'Membru foun aumenta ona. Hein aprovasaun.')
			duplikadu = Membro.objects.filter(nome__iexact=instance.nome, date_of_birth=instance.date_of_birth).exclude(pk=instance.pk)
			if duplikadu.exists():
				messages.warning(request, f'Atensaun: iha membru seluk ho naran no data moris hanesan ({duplikadu.first()}). Verifika!')
			return redirect('membro-detail', instance.hashed)
	else:
		form = MembroForm(user=request.user)
	context = {
		'form': form, 'group': group, 'cancel_url': '/membro/',
		'back_url': 'membro-list', 'back_label': 'Lista Membru',
		'title': 'Aumenta Membru', 'legend': 'Aumenta Membru'
	}
	return render(request, 'membro/form.html', context)


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def MembroUpdate(request, hashid):
	group = c_user_group(request.user)
	obj = get_object_or_404(membro_scope(request.user), hashed=hashid)
	old = snapshot(obj)
	if request.method == 'POST':
		form = MembroForm(request.POST, request.FILES, instance=obj, user=request.user)
		if form.is_valid():
			if not form.has_changed():
				messages.info(request, 'Laiha mudansa.')
				return redirect('membro-detail', hashid)
			instance = form.save(commit=False)
			instance.aprovasaun = 'Pendente'
			instance.aprovadu_husi = None
			instance.data_aprovasaun = None
			instance.razaun_rejeita = None
			instance.datetime = timezone.now()
			instance.user = request.user
			instance.save()
			log_historia(request.user, instance, 'Edita', diff_snapshot(old, snapshot(instance)) or 'Fotu troka')
			sinkroniza_login(instance)
			notif_aprovador(f'Data membru atualiza, hein aprovasaun foun: {instance.nome}', f'/membro/{instance.hashed}/')
			messages.success(request, 'Data membru atualiza ona. Hein aprovasaun foun.')
			return redirect('membro-detail', hashid)
	else:
		form = MembroForm(instance=obj, user=request.user)
	context = {
		'form': form, 'group': group, 'hashid': hashid, 'cancel_url': f'/membro/{hashid}/',
		'back_url': 'membro-list', 'back_label': 'Lista Membru',
		'title': 'Edita Membru', 'legend': 'Edita Membru'
	}
	return render(request, 'membro/form.html', context)


@login_required
@allowed_users(allowed_roles=roles.APROVA_ROLES)
@require_POST
def MembroDel(request, hashid):
	obj = get_object_or_404(membro_scope(request.user), hashed=hashid)
	nome = str(obj)
	desativa_login(obj)
	log_historia(request.user, None, 'Hamoos', f'Data membru hamoos: {nome}', nome=nome)
	if obj.image:
		obj.image.delete(save=False)
	obj.delete()
	messages.warning(request, 'Hamoos ho Susesu!.')
	return redirect('membro-list')


@login_required
@allowed_users(allowed_roles=roles.ALOKA_ROLES)
def MembroSearch(request):
	"""Opsaun <option> ba pesquiza membru (naran ka nu. eleitoral) iha form aloka pozisaun."""
	from django.db.models import Q
	q = (request.GET.get('q') or '').strip()
	objects = []
	if len(q) >= 2:
		base = Membro.objects.filter(aprovasaun='Aprovadu', status='Ativu')
		if c_user_group(request.user) == roles.PRES_ORG:
			scope = c_user_scope(request.user)
			base = base.filter(organizasaun_id=scope.organizasaun_id if scope else None)
		objects = base.filter(
			Q(nome__icontains=q) | Q(nu_eleitoral__icontains=q)).select_related('village', 'aldeia')[:30]
	return render(request, 'membro/search_options.html', {'objects': objects})


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def MembroKartaun(request, hashid):
	"""Kartaun membru (ID card) ne'ebé bele imprime. Deit ba membru aprovadu."""
	from custom.models import Organizasaun  # noqa: F401
	obj = get_object_or_404(membro_scope(request.user).select_related('organizasaun'), hashed=hashid, aprovasaun='Aprovadu')
	alokasauns = Alokasaun.objects.filter(membro=obj, ativu='Sim').select_related(
		'departamentu__organizasaun', 'municipality', 'post', 'village', 'aldeia', 'organizasaun')
	org = obj.organizasaun
	context = {
		'group': c_user_group(request.user), 'obj': obj, 'alokasauns': alokasauns, 'hashid': hashid,
		'logo_org': org.logo.url if org and org.logo else None,
		'title': 'Kartaun Membru', 'legend': 'Kartaun Membru'
	}
	return render(request, 'membro/kartaun.html', context)
