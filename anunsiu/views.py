from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group
from anunsiu.forms import AnunsiuForm
from anunsiu.models import Anunsiu
from anunsiu.utils import anunsiu_ba, notifika

LIAU = roles.VIEW_ROLES + [roles.ADMIN]


def _bele_edita(user, a):
	group = c_user_group(user)
	return group == roles.PRESIDENTE or (a.kria_husi_id == user.pk and group in roles.ANUNSIU_ROLES)


@login_required
@allowed_users(allowed_roles=LIAU)
def AnunsiuList(request):
	group = c_user_group(request.user)
	objects = list(anunsiu_ba(request.user).select_related('kria_husi', 'municipality', 'organizasaun', 'departamentu'))
	for a in objects:
		a.bele_edita = _bele_edita(request.user, a)
	context = {'group': group, 'objects': objects, 'can_add': group in roles.ANUNSIU_ROLES, 'title': 'Anunsiu', 'legend': 'Anunsiu'}
	return render(request, 'anunsiu/list.html', context)


def _form(request, instance=None):
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = AnunsiuForm(request.POST, instance=instance, user=request.user)
		if form.is_valid():
			a = form.save(commit=False)
			nova = a.pk is None
			if nova:
				a.kria_husi = request.user
			a.save()
			if nova:
				notifika(a)
			messages.success(request, 'Anunsiu rai ona.' + (' Notifikasaun haruka ona.' if nova else ''))
			return redirect('anunsiu-list')
	else:
		form = AnunsiuForm(instance=instance, user=request.user)
	legend = 'Edita Anunsiu' if instance else 'Anunsiu Foun'
	context = {'form': form, 'group': group, 'cancel_url': '/anunsiu/', 'back_url': 'anunsiu-list', 'back_label': 'Anunsiu',
		'title': legend, 'legend': legend}
	return render(request, 'anunsiu/form.html', context)


@login_required
@allowed_users(allowed_roles=roles.ANUNSIU_ROLES)
def AnunsiuAdd(request):
	return _form(request)


@login_required
@allowed_users(allowed_roles=roles.ANUNSIU_ROLES)
def AnunsiuUpdate(request, pk):
	a = get_object_or_404(Anunsiu, pk=pk)
	if not _bele_edita(request.user, a):
		return render(request, 'home/403.html', status=403)
	return _form(request, a)


@login_required
@allowed_users(allowed_roles=roles.ANUNSIU_ROLES)
@require_POST
def AnunsiuDel(request, pk):
	a = get_object_or_404(Anunsiu, pk=pk)
	if not _bele_edita(request.user, a):
		return render(request, 'home/403.html', status=403)
	a.delete()
	messages.warning(request, 'Anunsiu hamoos ona.')
	return redirect('anunsiu-list')
