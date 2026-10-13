import datetime
from django.db.models import Count
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from config import roles
from config.user_utils import c_user_group, membro_scope


class IsViewRole(BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_authenticated and c_user_group(request.user) in roles.VIEW_ROLES)


class BaseAPI(APIView):
	authentication_classes = [SessionAuthentication]
	permission_classes = [IsAuthenticated, IsViewRole]
	field = None

	def grouped(self, field):
		qs = membro_scope(self.request.user).order_by().values_list(field).annotate(n=Count('id', distinct=True)).order_by(field)
		return [str(x[0]) if x[0] is not None else 'Laiha' for x in qs], [x[1] for x in qs]

	def get(self, request, format=None):
		label, obj = self.grouped(self.field)
		return Response({'label': label, 'obj': obj})


class APIGender(BaseAPI):
	field = 'sex'


class APIAprovasaun(BaseAPI):
	field = 'aprovasaun'


class APIMunisipiu(BaseAPI):
	field = 'municipality__name'


class APIPostu(BaseAPI):
	field = 'post__name'


class APISuku(BaseAPI):
	field = 'village__name'


class APIAldeia(BaseAPI):
	field = 'aldeia__name'


class APIOrganizasaun(BaseAPI):
	field = 'organizasaun__code'


class APIStatus(BaseAPI):
	field = 'status'


class APIMarital(BaseAPI):
	field = 'marital'


class APIHakbit(BaseAPI):
	"""Membru tuir tinan tama PLP (tinan data_hakbit); ne'ebé laiha data la konta."""

	def get(self, request, format=None):
		qs = membro_scope(request.user).filter(data_hakbit__isnull=False)
		rows = qs.order_by().values_list('data_hakbit__year').annotate(n=Count('id', distinct=True)).order_by('data_hakbit__year')
		return Response({'label': [str(r[0]) for r in rows], 'obj': [r[1] for r in rows]})


AGE_BINS = [(0, 17, '< 18'), (18, 25, '18-25'), (26, 35, '26-35'), (36, 45, '36-45'),
	(46, 55, '46-55'), (56, 65, '56-65'), (66, 200, '> 65')]


class APIAge(BaseAPI):
	def get(self, request, format=None):
		today = datetime.date.today()
		counts = [0] * len(AGE_BINS)
		for dob in membro_scope(request.user).values_list('date_of_birth', flat=True).distinct():
			age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
			for i, (lo, hi, _) in enumerate(AGE_BINS):
				if lo <= age <= hi:
					counts[i] += 1
					break
		return Response({'label': [b[2] for b in AGE_BINS], 'obj': counts})
