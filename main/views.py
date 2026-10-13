from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from config import roles
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
		'title': 'Varanda', 'legend': 'Varanda'
	}
	return render(request, 'home/home.html', context)


def error_403(request, exception=None):
	return render(request, 'home/403.html', status=403)


def error_404(request, exception=None):
	return render(request, 'home/404.html', status=404)


def error_500(request):
	return render(request, 'home/500.html', status=500)
