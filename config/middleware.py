from django.contrib import messages
from django.shortcuts import redirect

LIBRE = ('/static/', '/media/', '/password/', '/logout/')


class TrokaPasswordMiddleware:
	"""Uzuáriu ho password foun husi Admin ka husi 'Kria login' tenke troka password molok uza sistema."""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		user = getattr(request, 'user', None)
		if user is not None and user.is_authenticated and not request.path.startswith(LIBRE):
			from user.models import UserScope
			if UserScope.objects.filter(user=user, troka_password=True).exists():
				messages.warning(request, 'Favór troka password uluk molok kontinua.')
				return redirect('change-password')
		return self.get_response(request)
