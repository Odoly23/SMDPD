"""
Import wilayah (Munisipiu, Postu Administrativu, Suku, Aldeia) husi file CSV (Diploma Ministerial 31/2026).
Fonte dadus: repositóriu SMKRE (`custom/data/`).

	python manage.py import_wilayah --dry-run
	python manage.py import_wilayah
	python manage.py import_wilayah /dalan/ba/pasta   # pasta ho munisipiu.csv no wilayah/*.csv

Seguru atu la'o dala barak (update_or_create tuir kódigu). Munisipiu ne'ebé iha ona (ex. husi seed
antigu) sei uza fali tuir naran. Suku ho postu_code mamuk la tama.
"""
import csv
import re
import unicodedata
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from custom.models import Municipality, AdministrativePost, Village, Aldeia

DATA_DIR = Path(settings.BASE_DIR) / 'custom' / 'data'

# Xave mapa Highcharts (countries/tl/tl-all) tuir kódigu munisipiu. Ataúro seidauk iha iha mapa.
HCKEY = {
	'AIL': 'tl-al', 'AIN': 'tl-an', 'BAU': 'tl-bc', 'BOB': 'tl-bb', 'COV': 'tl-cl', 'DIL': 'tl-dl', 'ERM': 'tl-er',
	'LAU': 'tl-bt', 'LIQ': 'tl-lq', 'MAN': 'tl-mt', 'MNF': 'tl-mf', 'OEC': 'tl-am', 'VIQ': 'tl-vq', 'ATA': '',
}


def lee_csv(path):
	with open(path, encoding='utf-8-sig') as f:
		return list(csv.DictReader(f))


def norma(naran):
	"""Naran sem asentu, espasu no parêntese, atu hetan munisipiu ne'ebé iha ona."""
	s = unicodedata.normalize('NFKD', naran or '').encode('ascii', 'ignore').decode().lower()
	s = re.sub(r'\(.*?\)', '', s)
	s = re.sub(r'[^a-z0-9]', '', s)
	return 'oecusse' if s.startswith('oecusse') else s


class Command(BaseCommand):
	help = "Import Munisipiu, Postu, Suku no Aldeia husi CSV (SMKRE, DM 31/2026). Seguru atu la'o dala barak."

	def add_arguments(self, parser):
		parser.add_argument('fonte', nargs='?', default=str(DATA_DIR), help='Pasta ho munisipiu.csv no wilayah/*.csv (default: custom/data)')
		parser.add_argument('--dry-run', action='store_true', help="Haree rezultadu deit, la rai buat ida")

	def handle(self, *args, **opt):
		base = Path(opt['fonte'])
		if not base.is_dir():
			raise CommandError(f'Pasta la iha: {base}')
		wil = base / 'wilayah'
		try:
			dados = {
				'munisipiu': lee_csv(base / 'munisipiu.csv'),
				'postu': lee_csv(next(wil.glob('postu_*.csv'))),
				'suku': lee_csv(next(wil.glob('suku_*.csv'))),
				'aldeia': lee_csv(next(wil.glob('aldeia_*.csv'))),
			}
		except (FileNotFoundError, StopIteration) as e:
			raise CommandError(f'File CSV la hetan iha {base}: {e}')
		with transaction.atomic():
			res = self.importa(dados)
			if opt['dry_run']:
				transaction.set_rollback(True)
		self.relatoriu(res, opt['dry_run'])

	def importa(self, d):
		r = {'mun': 0, 'postu': 0, 'suku': 0, 'aldeia': 0, 'verifika': [], 'erru': []}
		existe = {norma(m.name): m for m in Municipality.objects.all()}
		mun = {}
		for m in d['munisipiu']:
			code = m['code'].strip()
			obj = Municipality.objects.filter(code=code).first() or existe.get(norma(m['name']))
			if obj is None:
				obj = Municipality(code=code)
				r['mun'] += 1
			obj.code, obj.name, obj.hckey = code, m['name'].strip(), HCKEY.get(code, obj.hckey if obj.pk else '')
			obj.save()
			mun[code] = obj

		postu = {}
		for p in d['postu']:
			m = mun.get(p['munisipiu'])
			if not m:
				r['erru'].append(f'Postu {p["code"]}: munisipiu {p["munisipiu"]} la iha')
				continue
			obj, foun = AdministrativePost.objects.update_or_create(code=p['code'], defaults={'name': p['name'].strip(), 'municipality': m})
			r['postu'] += int(foun)
			postu[p['code']] = obj

		suku = {}
		for s in d['suku']:
			code = s['suku_code']
			if not s.get('postu_code'):
				r['verifika'].append(f"{code} {s['suku']}")
				continue
			p = postu.get(s['postu_code'])
			if not p:
				r['erru'].append(f'{code} {s["suku"]}: postu_code "{s["postu_code"]}" la iha')
				continue
			obj, foun = Village.objects.update_or_create(code=code, defaults={'name': s['suku'].strip(), 'administrativepost': p})
			r['suku'] += int(foun)
			suku[code] = obj

		for a in d['aldeia']:
			v = suku.get(a['suku_code'])
			if not v:
				continue
			_, foun = Aldeia.objects.update_or_create(code=a['aldeia_code'], defaults={'name': a['aldeia'].strip(), 'village': v})
			r['aldeia'] += int(foun)
		r['total'] = (Municipality.objects.count(), AdministrativePost.objects.count(), Village.objects.count(), Aldeia.objects.count())
		return r

	def relatoriu(self, r, dry):
		for e in r['erru']:
			self.stderr.write(self.style.ERROR(f'ERRU: {e}'))
		if r['verifika']:
			self.stdout.write(self.style.WARNING(f"{len(r['verifika'])} suku seidauk iha postu (VERIFIKA) — la tama."))
		self.stdout.write(self.style.SUCCESS(
			f"{'[DRY-RUN] ' if dry else ''}Foun: munisipiu {r['mun']}, postu {r['postu']}, suku {r['suku']}, aldeia {r['aldeia']}. "
			"Total: {} munisipiu, {} postu, {} suku, {} aldeia.".format(*r['total'])))
