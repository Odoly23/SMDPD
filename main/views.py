import time
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from config import roles
from django.utils import timezone
from anunsiu.utils import anunsiu_ba
from eventu.utils import eventu_ba
from report.views.view_2 import aniversariu_ba
from config.user_utils import c_user_group, c_user_scope, membro_scope
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun
from membro.models import Alokasaun


def _counts(user):
	return membro_scope(user).aggregate(
		total=Count('id', distinct=True),
		mane=Count('id', filter=Q(sex='Mane'), distinct=True),
		feto=Count('id', filter=Q(sex='Feto'), distinct=True),
		pendente=Count('id', filter=Q(aprovasaun='Pendente'), distinct=True),
		aprovadu=Count('id', filter=Q(aprovasaun='Aprovadu'), distinct=True),
		rejeitadu=Count('id', filter=Q(aprovasaun='Rejeitadu'), distinct=True),
	)


def _painel(user, group):
	"""Dadus painel (estilu repozitóriu): total, rezumu área, kuadru departamentu/orgaun no grafik, tuir peran no área user."""
	scope = c_user_scope(user)
	qs = membro_scope(user)
	ids = qs.values('pk')
	# rezumu área: unidade mínimu ne'ebé user nia área iha okos
	if group in roles.MUN_ROLES and scope and scope.municipality_id:
		titulu, unidade, campu, param = 'Postu', AdministrativePost.objects.filter(municipality_id=scope.municipality_id), 'post', 'post'
	elif group in roles.POSTU_ROLES and scope and scope.post_id:
		titulu, unidade, campu, param = 'Suku', Village.objects.filter(administrativepost_id=scope.post_id), 'village', 'village'
	elif group in roles.SUKU_ROLES and scope and scope.village_id:
		titulu, unidade, campu, param = 'Aldeia', Aldeia.objects.filter(village_id=scope.village_id), 'aldeia', 'aldeia'
	elif group in roles.ALDEIA_ROLES:
		titulu, unidade, campu, param = 'Sexu', None, 'sex', 'sex'
	else:
		titulu, unidade, campu, param = 'Munisipiu', Municipality.objects.all(), 'municipality', 'municipality'
	if unidade is None:
		hira = {r['sex']: r['n'] for r in qs.values('sex').annotate(n=Count('id', distinct=True))}
		area = [{'naran': 'Mane', 'total': hira.get('Mane', 0), 'param': 'sex', 'valor': 'Mane'},
			{'naran': 'Feto', 'total': hira.get('Feto', 0), 'param': 'sex', 'valor': 'Feto'}]
	else:
		hira = {r[campu + '_id']: r['n'] for r in qs.values(campu + '_id').annotate(n=Count('id', distinct=True))}
		area = [{'naran': u.name, 'total': hira.get(u.pk, 0), 'param': param, 'valor': u.pk} for u in unidade]
	# departamentu ne'ebé user bele hare
	deps = Departamentu.objects.filter(is_active=True).select_related('organizasaun')
	orgs = Organizasaun.objects.filter(is_active=True)
	if group in roles.DEP_ROLES:
		deps = deps.filter(pk=scope.departamentu_id) if scope else deps.none()
		orgs = orgs.none()
	elif group in roles.ORG_ROLES:
		deps = deps.filter(organizasaun_id=scope.organizasaun_id) if scope else deps.none()
		orgs = orgs.filter(pk=scope.organizasaun_id) if scope else orgs.none()
	hira_dep = {r['departamentu_id']: r['n'] for r in Alokasaun.objects.filter(
		nivel='Departamentu', ativu='Sim', membro_id__in=ids).values('departamentu_id').annotate(n=Count('membro', distinct=True))}
	departamentu = [{'naran': str(d), 'total': hira_dep.get(d.pk, 0), 'id': d.pk} for d in deps]
	hira_org = {r['organizasaun_id']: r['n'] for r in qs.values('organizasaun_id').annotate(n=Count('id', distinct=True))}
	orgaun = [{'naran': o.name, 'total': hira_org.get(o.pk, 0), 'id': o.pk} for o in orgs]
	grafik = departamentu or area
	return {
		'titulu_area': titulu, 'area': area, 'departamentus': departamentu, 'orgauns': orgaun,
		'grafik_titulu': 'Total Membru por Departamentu' if departamentu else 'Total Membru por ' + titulu,
		'grafik_label': [g['naran'] for g in grafik], 'grafik_data': [g['total'] for g in grafik],
	}


@login_required
def home(request):
	group = c_user_group(request.user)
	context = {
		'group': group,
		'counts': _counts(request.user) if group in roles.VIEW_ROLES else None,
		'anunsius': list(anunsiu_ba(request.user)[:3]) if group else [],
		'aniversarius': aniversariu_ba(request.user, 7)[:5] if group in roles.VIEW_ROLES else [],
		'eventus': list(eventu_ba(request.user).filter(data_hahu__gte=timezone.now()).order_by('data_hahu')[:3]) if group in roles.VIEW_ROLES else [],
		'title': 'Varanda', 'legend': 'Varanda'
	}
	if group in roles.VIEW_ROLES:
		context.update(_painel(request.user, group))
	return render(request, 'home/home.html', context)


class LoginTap(auth_views.LoginView):
	"""Login ho limitasaun tentativa sala (5 dala / 10 minutu) no 2FA (se uzuáriu aktiva ona)."""
	template_name = 'home/login.html'
	redirect_authenticated_user = True

	def post(self, request, *args, **kwargs):
		from config.security import bloku, rai_log
		if bloku(request.POST.get('username'), request):
			rai_log(request, request.POST.get('username'), 'Bloku')
			form = self.get_form()
			form.add_error(None, 'Tentativa sala barak liu. Hein minutu 10 no koko fali.')
			return self.render_to_response(self.get_context_data(form=form, bloku=True), status=429)
		return super().post(request, *args, **kwargs)

	def form_valid(self, form):
		from config.models import Totp
		user = form.get_user()
		if Totp.objects.filter(user=user, aktivu=True).exists():
			self.request.session['pre2fa'] = {
				'uid': user.pk, 'backend': getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend'),
				'next': self.get_success_url(), 'ts': time.time()}
			return redirect('login-2fa')
		return super().form_valid(form)


class PasswordTroka(auth_views.PasswordChangeView):
	template_name = 'auth/change_password.html'
	success_url = '/password/done/'

	def form_valid(self, form):
		from user.models import UserScope
		UserScope.objects.filter(user=self.request.user).update(troka_password=False)
		return super().form_valid(form)

	def get_context_data(self, **kwargs):
		from user.models import UserScope
		ctx = super().get_context_data(**kwargs)
		ctx['tenke'] = UserScope.objects.filter(user=self.request.user, troka_password=True).exists()
		return ctx


def error_403(request, exception=None):
	return render(request, 'home/403.html', status=403)


def error_404(request, exception=None):
	return render(request, 'home/404.html', status=404)


def error_500(request):
	return render(request, 'home/500.html', status=500)
