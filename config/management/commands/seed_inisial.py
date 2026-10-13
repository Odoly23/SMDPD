import os
import secrets
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from config import roles
from custom.models import Municipality

MUNISIPIU = [
	('Aileu', 'AL'), ('Ainaro', 'AN'), ('Baucau', 'BC'), ('Bobonaro', 'BB'), ('Cova Lima', 'CL'),
	('Dili', 'DI'), ('Ermera', 'ER'), ('Lautem', 'LT'), ('Liquica', 'LQ'), ('Manatuto', 'MT'),
	('Manufahi', 'MF'), ('Oecusse', 'OE'), ('Viqueque', 'VQ'), ('Atauro', 'AT'),
]


class Command(BaseCommand):
	help = 'Isi data inisial: peran (group), munisipiu Timor-Leste no user admin.'

	def handle(self, *args, **options):
		for key, _ in roles.ROLE_LABELS:
			Group.objects.get_or_create(name=key)
		for name, code in MUNISIPIU:
			Municipality.objects.get_or_create(name=name, defaults={'code': code})
		user = User.objects.filter(username='admin').first()
		if not user:
			password = os.environ.get('ADMIN_PASSWORD') or secrets.token_urlsafe(12)
			user = User.objects.create_user('admin', password=password, first_name='Administrador')
			user.groups.add(Group.objects.get(name=roles.ADMIN))
			if not os.environ.get('ADMIN_PASSWORD'):
				self.stdout.write(self.style.WARNING(f'User admin kria ona. Password: {password}  (hakerek, sei hatudu dala ida deit)'))
			else:
				self.stdout.write('User admin kria ona ho ADMIN_PASSWORD.')
		self.stdout.write(self.style.SUCCESS('Seed inisial remata.'))
