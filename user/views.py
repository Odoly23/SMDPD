from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from config import roles
from config.decorators import allowed_users
import secrets
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from config.models import LoginLog, Totp, KodeRekupera
from config.user_utils import c_user_group
from user.forms import UserForm

ROLE_NAME = dict(roles.ROLE_LABELS)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def UserList(request):
	group = c_user_group(request.user)
	users = User.objects.prefetch_related('groups').select_related(
		'scope__departamentu', 'scope__municipality', 'scope__post', 'scope__village', 'scope__aldeia', 'scope__organizasaun').order_by('username')
	objects = []
	for u in users:
		role = u.groups.all()[0].name if u.groups.all() else None
		scope = getattr(u, 'scope', None)
		area = (scope.departamentu or scope.aldeia or scope.village or scope.post or scope.municipality or scope.organizasaun) if scope else None
		objects.append({'obj': u, 'role': ROLE_NAME.get(role, role or '-'), 'area': area or '-'})
	ativu_2fa = set(Totp.objects.filter(aktivu=True).values_list('user_id', flat=True))
	for o in objects:
		o['dua_faktor'] = o['obj'].pk in ativu_2fa
	context = {
		'group': group, 'objects': objects,
		'title': 'Lista Uzuáriu', 'legend': 'Lista Uzuáriu'
	}
	return render(request, 'user/list.html', context)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def UserAdd(request):
	group = c_user_group(request.user)
	if request.method == 'POST':
		form = UserForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Uzuáriu foun aumenta ona.')
			return redirect('user-list')
	else:
		form = UserForm()
	context = {
		'form': form, 'group': group, 'cancel_url': '/user/',
		'back_url': 'user-list', 'back_label': 'Lista Uzuáriu',
		'title': 'Aumenta Uzuáriu', 'legend': 'Aumenta Uzuáriu'
	}
	return render(request, 'user/form.html', context)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def UserUpdate(request, pk):
	group = c_user_group(request.user)
	obj = get_object_or_404(User, pk=pk)
	if request.method == 'POST':
		form = UserForm(request.POST, instance=obj)
		if form.is_valid():
			if obj.pk == request.user.pk and (not form.cleaned_data['is_active'] or form.cleaned_data['group'] != roles.ADMIN):
				form.add_error(None, 'La bele desativa ka troka peran ba ita nia an rasik.')
			else:
				form.save()
				messages.success(request, 'Uzuáriu atualiza ona.')
				return redirect('user-list')
	else:
		form = UserForm(instance=obj)
	context = {
		'form': form, 'group': group, 'cancel_url': '/user/',
		'back_url': 'user-list', 'back_label': 'Lista Uzuáriu',
		'title': 'Edita Uzuáriu', 'legend': 'Edita Uzuáriu'
	}
	return render(request, 'user/form.html', context)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
@require_POST
def UserResetPassword(request, pk):
	"""Admin reset password: password temporáriu hatudu dala ida deit, uzuáriu tenke troka bainhira login."""
	from user.models import UserScope
	obj = get_object_or_404(User, pk=pk)
	if obj.pk == request.user.pk:
		messages.error(request, 'Uza Troka Password ba ita nia konta rasik.')
		return redirect('user-list')
	password = secrets.token_urlsafe(9)
	obj.set_password(password)
	obj.is_active = True
	obj.save()
	UserScope.objects.update_or_create(user=obj, defaults={'troka_password': True})  # nosec B105
	LoginLog.objects.create(user=obj, username=obj.username, hasil='Reset', user_agent=f'husi Admin {request.user.username}')
	context = {'group': c_user_group(request.user), 'akun': obj, 'password': password, 'title': 'Password Foun', 'legend': 'Password Foun'}
	return render(request, 'user/reset.html', context)


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
@require_POST
def UserReset2fa(request, pk):
	"""Admin hamoos 2FA (ez. uzuáriu perde telemovel)."""
	obj = get_object_or_404(User, pk=pk)
	Totp.objects.filter(user=obj).delete()
	KodeRekupera.objects.filter(user=obj).delete()
	LoginLog.objects.create(user=obj, username=obj.username, hasil='Reset 2FA', user_agent=f'husi Admin {request.user.username}')
	messages.success(request, f'2FA {obj.username} hamoos ona.')
	return redirect('user-list')


@login_required
@allowed_users(allowed_roles=[roles.ADMIN])
def UserLog(request):
	"""Log login: susesu, sala, bloku, 2FA no reset (auditoria seguransa)."""
	qs = LoginLog.objects.select_related('user')
	hasil = request.GET.get('hasil')
	if hasil:
		qs = qs.filter(hasil=hasil)
	q = (request.GET.get('q') or '').strip()
	if q:
		qs = qs.filter(Q(username__icontains=q) | Q(ip__icontains=q))
	page = Paginator(qs, 50).get_page(request.GET.get('page'))
	params = request.GET.copy()
	params.pop('page', None)
	context = {'group': c_user_group(request.user), 'page': page, 'hasil': hasil or '', 'q': q, 'qs': params.urlencode(),
		'hasils': LoginLog.objects.order_by().values_list('hasil', flat=True).distinct(), 'title': 'Log Login', 'legend': 'Log Login'}
	return render(request, 'user/log.html', context)
