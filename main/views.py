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
from config.user_utils import c_user_group, membro_scope


def _counts(user):
	return membro_scope(user).aggregate(
		total=Count('id', distinct=True),
		mane=Count('id', filter=Q(sex='Mane'), distinct=True),
		feto=Count('id', filter=Q(sex='Feto'), distinct=True),
		pendente=Count('id', filter=Q(aprovasaun='Pendente'), distinct=True),
		aprovadu=Count('id', filter=Q(aprovasaun='Aprovadu'), distinct=True),
		rejeitadu=Count('id', filter=Q(aprovasaun='Rejeitadu'), distinct=True),
	)


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
