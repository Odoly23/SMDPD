from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from config.user_utils import c_user_group
from notif.models import Notifikasaun


@login_required
def NotifList(request):
	objects = Notifikasaun.objects.filter(user=request.user)[:200]
	context = {
		'group': c_user_group(request.user), 'objects': objects,
		'title': 'Notifikasaun', 'legend': 'Notifikasaun'
	}
	return render(request, 'notif/list.html', context)


@login_required
def NotifLoke(request, pk):
	obj = get_object_or_404(Notifikasaun, pk=pk, user=request.user)
	obj.is_read = True
	obj.save(update_fields=['is_read'])
	if obj.url.startswith('/') and not obj.url.startswith('//') and '\\' not in obj.url:
		return redirect(obj.url)
	return redirect('notif-list')


@login_required
@require_POST
def NotifLe(request):
	Notifikasaun.objects.filter(user=request.user, is_read=False).update(is_read=True)
	messages.success(request, 'Notifikasaun hotu marka ona hanesan lee ona.')
	return redirect('notif-list')
