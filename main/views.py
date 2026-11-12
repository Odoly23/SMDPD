import time
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.http import Http404
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


def entitas_ba(user, group=None):
	"""Entidade (PLP Nasionál no orgaun/movimentu) ne'ebé user bele hare: [(kode, Organizasaun|None)]."""
	group = group or c_user_group(user)
	scope = c_user_scope(user)
	if group in roles.DEP_ROLES:
		dep = scope.departamentu if scope and scope.departamentu_id else None
		if not dep:
			return []
		return [('orgaun', dep.organizasaun)] if dep.organizasaun_id else [('nasional', None)]
	if group in roles.ORG_ROLES:
		return [('orgaun', scope.organizasaun)] if scope and scope.organizasaun_id and scope.organizasaun.is_active else []
	if group in roles.VIEW_ROLES:
		return [('nasional', None)] + [('orgaun', o) for o in Organizasaun.objects.filter(is_active=True)]
	return []


def _presidente_husi(alokasauns):
	"""Naran presidente primeiru husi lista alokasaun (ho select_related membro)."""
	for a in alokasauns:
		if a.pozisaun == 'Presidente':
			return a.membro.nome
	return ''


def _tinan_filtru(qs, tinan, mode):
	if mode == 'foun':
		return qs.filter(data_hakbit__year=tinan)
	return qs.filter(status='Ativu').filter(Q(data_hakbit__isnull=True) | Q(data_hakbit__year__lte=tinan))


def _painel(user, group, tinan, mode):
	"""Dadus painel (estilu repozitóriu): total, rezumu área, entidade (PLP/orgaun) no grafik Mane x Feto, tuir peran no área user."""
	scope = c_user_scope(user)
	qs = membro_scope(user)
	if group in roles.MUN_ROLES and scope and scope.municipality_id:
		titulu, unidade, campu, param = 'Postu', AdministrativePost.objects.filter(municipality_id=scope.municipality_id), 'post', 'post'
	elif group in roles.POSTU_ROLES and scope and scope.post_id:
		titulu, unidade, campu, param = 'Suku', Village.objects.filter(administrativepost_id=scope.post_id), 'village', 'village'
	elif group in roles.SUKU_ROLES and scope and scope.village_id:
		titulu, unidade, campu, param = 'Aldeia', Aldeia.objects.filter(village_id=scope.village_id), 'aldeia', 'aldeia'
	elif group in roles.ALDEIA_ROLES:
		titulu, unidade, campu, param = 'Aldeia', None, 'sex', 'sex'
	else:
		titulu, unidade, campu, param = 'Munisipiu', Municipality.objects.all(), 'municipality', 'municipality'
	if unidade is None:
		hira = {r['sex']: r['n'] for r in qs.values('sex').annotate(n=Count('id', distinct=True))}
		area = [{'naran': 'Mane', 'total': hira.get('Mane', 0), 'param': 'sex', 'valor': 'Mane'},
			{'naran': 'Feto', 'total': hira.get('Feto', 0), 'param': 'sex', 'valor': 'Feto'}]
	else:
		hira = {r[campu + '_id']: r['n'] for r in qs.values(campu + '_id').annotate(n=Count('id', distinct=True))}
		area = [{'naran': u.name, 'total': hira.get(u.pk, 0), 'param': param, 'valor': u.pk} for u in unidade]

	# entidade: PLP Nasionál no orgaun/movimentu ho nia presidente no total membru
	lista = entitas_ba(user, group)
	lider = {}
	for a in Alokasaun.objects.filter(ativu='Sim', pozisaun='Presidente', nivel__in=['Nasional', 'Organizasaun']).select_related('membro'):
		if a.nivel == 'Nasional':
			lider.setdefault(None, a.membro.nome)
		elif a.municipality_id is None:
			lider.setdefault(a.organizasaun_id, a.membro.nome)
	hira_org = {r['organizasaun_id']: r['n'] for r in qs.values('organizasaun_id').annotate(n=Count('id', distinct=True))}
	entidades = []
	for kode, org in lista:
		if kode == 'nasional':
			entidades.append({'naran': 'PLP Nasionál', 'total': qs.count(), 'lider': lider.get(None, ''), 'url': reverse('entidade-nasional'),
				'logo': static('main/images/logo_plp.png')})
		else:
			entidades.append({'naran': org.name, 'total': hira_org.get(org.pk, 0), 'lider': lider.get(org.pk, ''), 'url': reverse('entidade-orgaun', args=[org.hashed]),
				'logo': org.logo.url if org.logo else static('main/images/logo_plp.png')})

	# grafik Mane x Feto tuir área, ba tinan ativu (membru aprovadu)
	base = _tinan_filtru(qs.filter(aprovasaun='Aprovadu'), tinan, mode)
	sen_area = 0
	if unidade is None:
		hira_sex = {r['sex']: r['n'] for r in base.values('sex').annotate(n=Count('id', distinct=True))}
		g_label, mane, feto = [str(scope.aldeia) if scope and scope.aldeia_id else 'Aldeia'], [hira_sex.get('Mane', 0)], [hira_sex.get('Feto', 0)]
	else:
		cont = {}
		for r in base.values(campu + '_id', 'sex').annotate(n=Count('id', distinct=True)):
			cont[(r[campu + '_id'], r['sex'])] = r['n']
		g_label = [u.name for u in unidade]
		sen_area = base.filter(**{campu + '_id__isnull': True}).count()
		mane = [cont.get((u.pk, 'Mane'), 0) for u in unidade]
		feto = [cont.get((u.pk, 'Feto'), 0) for u in unidade]
	tinan_ida = qs.exclude(data_hakbit__isnull=True).order_by('data_hakbit').values_list('data_hakbit__year', flat=True).first()
	agora = timezone.now().year
	return {
		'titulu_area': titulu, 'area': area, 'entidades': entidades,
		'tinan': tinan, 'mode': mode, 'tinan_lista': list(range(min(tinan_ida or agora, agora), agora + 1)),
		'grafik_titulu': ('Membru Foun Mane no Feto por %s iha Tinan %d' if mode == 'foun' else 'Membru Ativu Mane no Feto por %s to\'o Tinan %d') % (titulu, tinan),
		'grafik_label': g_label, 'grafik_mane': mane, 'grafik_feto': feto,
		'total_mane': sum(mane), 'total_feto': sum(feto), 'sen_area': sen_area,
	}


def _tinan_param(request):
	agora = timezone.now().year
	t = request.GET.get('tinan', '')
	tinan = int(t) if t.isdigit() and 1990 <= int(t) <= agora + 1 else agora
	mode = 'foun' if request.GET.get('mode') == 'foun' else 'hotu'
	return tinan, mode


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
		context.update(_painel(request.user, group, *_tinan_param(request)))
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


@login_required
def EntidadeDetail(request, hashid=None):
	"""Detallu entidade (PLP Nasionál ka orgaun/movimentu): lideransa (presidente, vice, sekretaria...) no tabela departamentu."""
	group = c_user_group(request.user)
	if group not in roles.VIEW_ROLES:
		raise Http404
	org = None
	if hashid:
		org = get_object_or_404(Organizasaun, hashed=hashid, is_active=True)
	if (('orgaun', org) if org else ('nasional', None)) not in entitas_ba(request.user, group):
		raise Http404
	scope = c_user_scope(request.user)
	qs = membro_scope(request.user)
	if org:
		qs = qs.filter(organizasaun=org)
		lideransa = Alokasaun.objects.filter(ativu='Sim', nivel='Organizasaun', organizasaun=org)
		deps = Departamentu.objects.filter(is_active=True, organizasaun=org)
	else:
		lideransa = Alokasaun.objects.filter(ativu='Sim', nivel='Nasional')
		deps = Departamentu.objects.filter(is_active=True, organizasaun__isnull=True)
	if group in roles.DEP_ROLES and scope:
		deps = deps.filter(pk=scope.departamentu_id)
	lideransa = sorted(lideransa.exclude(pozisaun='Membru').select_related('membro', 'municipality'), key=lambda a: (a.rank(), a.membro.nome))
	ids = membro_scope(request.user).values('pk')   # anggota departamentu bele laiha 'organizasaun' hanesan entidade
	total_dep = {r['departamentu_id']: r['n'] for r in Alokasaun.objects.filter(
		nivel='Departamentu', ativu='Sim', membro_id__in=ids).values('departamentu_id').annotate(n=Count('membro', distinct=True))}
	lider_dep = {}
	for a in Alokasaun.objects.filter(nivel='Departamentu', ativu='Sim', departamentu__in=deps).exclude(pozisaun='Membru').select_related('membro'):
		lider_dep.setdefault(a.departamentu_id, []).append(a)
	rows = []
	for d in deps:
		lid = sorted(lider_dep.get(d.pk, []), key=lambda a: a.rank())
		rows.append({'dep': d, 'presidente': next((a.membro.nome for a in lid if a.pozisaun == 'Presidente Departamentu'), ''),
			'seluk': [{'naran': a.membro.nome, 'pozisaun': a.pozisaun} for a in lid if a.pozisaun != 'Presidente Departamentu'],
			'total': total_dep.get(d.pk, 0)})
	hira_sex = {r['sex']: r['n'] for r in qs.values('sex').annotate(n=Count('id', distinct=True))}
	context = {
		'group': group, 'org': org, 'naran': org.name if org else 'PLP Nasionál',
		'logo': (org.logo.url if org and org.logo else static('main/images/logo_plp.png')),
		'total': qs.count(), 'mane': hira_sex.get('Mane', 0), 'feto': hira_sex.get('Feto', 0),
		'lideransa': lideransa, 'rows': rows,
		'filtru_membru': ('organizasaun=%d' % org.pk) if org else '',
		'title': org.name if org else 'PLP Nasionál', 'legend': org.name if org else 'PLP Nasionál',
	}
	return render(request, 'home/entidade.html', context)
