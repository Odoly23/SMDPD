from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, ProtectedError
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group
from custom.forms import MunicipalityForm, PostForm, VillageForm, AldeiaForm, DepartamentuForm, OrganizasaunForm
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun


# ---------- dropdown AJAX (Munisipiu -> Postu -> Suku -> Aldeia) ----------
def _opsaun(request, template, key, model, filtru):
	val = request.GET.get(key)
	objects = model.objects.filter(**{filtru: val}).order_by('name') if (val or '').isdigit() else []
	return render(request, template, {'objects': objects})


@login_required
def load_posts(request):
	return _opsaun(request, 'custom/dropdown.html', 'municipality', AdministrativePost, 'municipality_id')


@login_required
def load_villages(request):
	return _opsaun(request, 'custom/dropdown.html', 'post', Village, 'administrativepost_id')


@login_required
def load_aldeias(request):
	return _opsaun(request, 'custom/dropdown.html', 'village', Aldeia, 'village_id')


# ---------- data master (Admin) ----------
MASTER = {
	'munisipiu': {'model': Municipality, 'form': MunicipalityForm, 'label': 'Munisipiu'},
	'postu': {'model': AdministrativePost, 'form': PostForm, 'label': 'Postu'},
	'suku': {'model': Village, 'form': VillageForm, 'label': 'Suku'},
	'aldeia': {'model': Aldeia, 'form': AldeiaForm, 'label': 'Aldeia'},
	'departamentu': {'model': Departamentu, 'form': DepartamentuForm, 'label': 'Departamentu'},
	'organizasaun': {'model': Organizasaun, 'form': OrganizasaunForm, 'label': 'Orgaun/Movimentu'},
}


def _master(tipu):
	if tipu not in MASTER:
		raise Http404
	return MASTER[tipu]


def _rows(tipu):
	if tipu == 'munisipiu':
		qs = Municipality.objects.annotate(p=Count('administrativepost', distinct=True), m=Count('membro', distinct=True))
		return ['Kódigu', 'Naran Munisipiu', 'Xave Mapa', 'Total Postu', 'Total Membru'], [(o, [o.code or '-', o.name, o.hckey or '-', o.p, o.m]) for o in qs]
	if tipu == 'postu':
		qs = AdministrativePost.objects.select_related('municipality').annotate(v=Count('village', distinct=True), m=Count('membro', distinct=True))
		return ['Munisipiu', 'Naran Postu', 'Total Suku', 'Total Membru'], [(o, [o.municipality, o.name, o.v, o.m]) for o in qs]
	if tipu == 'suku':
		qs = Village.objects.select_related('administrativepost__municipality').annotate(a=Count('aldeia', distinct=True), m=Count('membro', distinct=True))
		return ['Munisipiu', 'Postu', 'Naran Suku', 'Total Aldeia', 'Total Membru'], [
			(o, [o.administrativepost.municipality, o.administrativepost, o.name, o.a, o.m]) for o in qs]
	if tipu == 'aldeia':
		qs = Aldeia.objects.select_related('village__administrativepost__municipality').annotate(m=Count('membro'))
		return ['Munisipiu', 'Postu', 'Suku', 'Naran Aldeia', 'Total Membru'], [
			(o, [o.village.administrativepost.municipality, o.village.administrativepost, o.village, o.name, o.m]) for o in qs]
	if tipu == 'departamentu':
		qs = Departamentu.objects.annotate(m=Count('alokasaun', distinct=True))
		return ['Kódigu', 'Naran', 'Ativu', 'Total Pozisaun'], [(o, [o.code, o.name, 'Sim' if o.is_active else 'Lae', o.m]) for o in qs]
	qs = Organizasaun.objects.annotate(m=Count('membro'))
	return ['Kódigu', 'Naran', 'Ativu', 'Total Membru'], [(o, [o.code, o.name, 'Sim' if o.is_active else 'Lae', o.m]) for o in qs]


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def MasterList(request, tipu):
	cfg = _master(tipu)
	headers, rows = _rows(tipu)
	context = {
		'group': c_user_group(request.user), 'tipu': tipu, 'headers': headers, 'rows': rows,
		'title': f'Lista {cfg["label"]}', 'legend': f'Lista {cfg["label"]}'
	}
	return render(request, 'custom/master_list.html', context)


def _master_form(request, tipu, instance=None):
	cfg = _master(tipu)
	if request.method == 'POST':
		form = cfg['form'](request.POST, instance=instance)
		if form.is_valid():
			form.save()
			messages.success(request, 'Rai ho Susesu!.')
			return redirect('master-list', tipu)
	else:
		form = cfg['form'](instance=instance)
	acao = 'Edita' if instance else 'Aumenta'
	context = {
		'form': form, 'group': c_user_group(request.user), 'cancel_url': f'/custom/master/{tipu}/',
		'back_url': 'master-list', 'back_args': [tipu], 'back_label': f'Lista {cfg["label"]}',
		'title': f'{acao} {cfg["label"]}', 'legend': f'{acao} {cfg["label"]}'
	}
	return render(request, 'main/form.html', context)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def MasterAdd(request, tipu):
	return _master_form(request, tipu)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def MasterUpdate(request, tipu, pk):
	obj = get_object_or_404(_master(tipu)['model'], pk=pk)
	return _master_form(request, tipu, obj)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
@require_POST
def MasterDel(request, tipu, pk):
	obj = get_object_or_404(_master(tipu)['model'], pk=pk)
	try:
		obj.delete()
		messages.warning(request, 'Hamoos ho Susesu!.')
	except ProtectedError:
		messages.error(request, 'La bele hamoos: iha data seluk ne\'ebé uza ona.')
	return redirect('master-list', tipu)
