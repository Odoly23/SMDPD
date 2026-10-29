from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

LIBRE = ('/static/', '/media/', '/password/', '/logout/', '/seguransa/', '/login/')


class SeguransaMiddleware:
	"""1) Password foun tenke troka uluk. 2) Peran sensitivu tenke iha 2FA (se DJANGO_2FA_WAJIBA). 3) Header seguransa no la cache pájina privadu."""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		user = getattr(request, 'user', None)
		autentikadu = user is not None and user.is_authenticated
		if autentikadu and not request.path.startswith(LIBRE):
			from user.models import UserScope
			if UserScope.objects.filter(user=user, troka_password=True).exists():
				messages.warning(request, 'Favór troka password uluk molok kontinua.')
				return redirect('change-password')
			if getattr(settings, 'SMDPD_2FA_WAJIBA', False) and self._wajiba(user):
				messages.warning(request, 'Peran ida-ne\'e tenke aktiva autentikasaun rua faktór (2FA) molok kontinua.')
				return redirect('seguransa-2fa')
		response = self.get_response(request)
		if not request.path.startswith(('/static/', '/media/')):
			response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
			if autentikadu or request.path.startswith(('/login/', '/seguransa/', '/password/')):
				response['Cache-Control'] = 'no-store, private'      # la rai pájina privadu iha cache browser
				response['Pragma'] = 'no-cache'
		return response

	@staticmethod
	def _wajiba(user):
		from config import roles
		from config.models import Totp
		from config.user_utils import c_user_group
		if c_user_group(user) not in (roles.ADMIN, roles.PRESIDENTE, roles.SEKRETARIA):
			return False
		return not Totp.objects.filter(user=user, aktivu=True).exists()
