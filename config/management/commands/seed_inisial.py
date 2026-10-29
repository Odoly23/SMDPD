import os
import secrets
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from config import roles
from django.core.management import call_command
from custom.models import Organizasaun

# Orgaun/Movimentu iha PLP (kódigu, naran)
ORGAUN = [
	('SEE', 'Sentru Estudu Estratejiku'), ('MATMR', 'Movimento Assegura TMR'),
	('MLBDF', "Movimento Loriko Buka Di'ik Funan"), ('MLP', 'Movimento Lorico Popular'),
	('MLS', 'Movimento Lorico Saudavel'), ('LFM', 'Lorico Forma (Forsa Matak)'),
	('RACA', 'Movimento RACA'), ('ADST', 'Assosiadu Defisiente Salva Timor'),
	('MDIA', 'Movimento Diaspora'), ('MLM', 'Movimento Loriko Matak'),
]


class Command(BaseCommand):
	help = 'Isi data inisial: peran (group), wilayah Timor-Leste (SMKRE), orgaun/movimentu no user admin.'

	def handle(self, *args, **options):
		for key, _ in roles.ROLE_LABELS:
			Group.objects.get_or_create(name=key)
		call_command('import_wilayah', stdout=self.stdout)  # munisipiu, postu, suku, aldeia (SMKRE)
		for code, name in ORGAUN:
			Organizasaun.objects.get_or_create(code=code, defaults={'name': name})
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
