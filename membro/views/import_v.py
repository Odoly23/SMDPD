import csv
import datetime
import io
from config.utils import CsvAman
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group
from custom.models import Aldeia, Organizasaun
from membro.forms import MembroForm
from membro.utils import log_historia
from notif.utils import notif_aprovador

MAX_BYTES = 1024 * 1024
MAX_ROWS = 1000
KOLUNA = ['nome', 'sex', 'date_of_birth', 'nu_eleitoral', 'aldeia_code', 'place_of_birth', 'marital', 'nu_bi', 'telefone',
	'address', 'organizasaun_code', 'data_hakbit', 'status']
OBRIGATORIU = ['nome', 'sex', 'date_of_birth', 'nu_eleitoral', 'aldeia_code']


def _data(valor):
	"""Aseita YYYY-MM-DD ka DD/MM/YYYY; fila string ISO (ka string original se la loos)."""
	v = (valor or '').strip()
	for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
		try:
			return datetime.datetime.strptime(v, fmt).date().isoformat()
		except ValueError:
			continue
	return v


def _baca(arkivu):
	teks = arkivu.read().decode('utf-8-sig')
	try:
		dialek = csv.Sniffer().sniff(teks[:2000], delimiters=',;\t')
	except csv.Error:
		dialek = csv.excel
	leitor = csv.DictReader(io.StringIO(teks), dialect=dialek)
	kab = [(k or '').strip().lower() for k in (leitor.fieldnames or [])]
	leitor.fieldnames = kab
	return kab, list(leitor)


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def MembroImportTemplate(request):
	response = HttpResponse(content_type='text/csv; charset=utf-8')
	response['Content-Disposition'] = 'attachment; filename="modelu_importa_membru.csv"'
	response.write('﻿')
	w = CsvAman(response)
	w.writerow(KOLUNA)
	w.writerow(['Joao da Silva', 'Mane', '1990-05-20', 'EL-000123', 'AIL-A0001', 'Aileu', 'Casado/a', '', '77123456', 'Rua A', '', '2020-01-15', 'Ativu'])
	return response


@login_required
@allowed_users(allowed_roles=roles.INPUT_ROLES)
def MembroImport(request):
	"""Importa membru barak husi CSV. Linha hotu tenke loos; se iha erru, laiha buat ida mak rai."""
	group = c_user_group(request.user)
	context = {'group': group, 'koluna': KOLUNA, 'obrigatoriu': OBRIGATORIU, 'max_rows': MAX_ROWS,
		'title': 'Importa Membru', 'legend': 'Importa Membru'}
	if request.method == 'POST':
		arkivu = request.FILES.get('arkivu')
		verifika = request.POST.get('verifika') == 'on'
		if not arkivu:
			messages.error(request, 'Hili file CSV uluk.')
			return render(request, 'membro/import.html', context)
		if arkivu.size > MAX_BYTES:
			messages.error(request, 'File boot liu 1 MB.')
			return render(request, 'membro/import.html', context)
		try:
			kab, linhas = _baca(arkivu)
		except UnicodeDecodeError:
			messages.error(request, 'File tenke UTF-8 (Save as CSV UTF-8).')
			return render(request, 'membro/import.html', context)
		falta = [k for k in OBRIGATORIU if k not in kab]
		if falta:
			messages.error(request, f'Koluna obrigatóriu la iha: {", ".join(falta)}.')
			return render(request, 'membro/import.html', context)
		if not linhas:
			messages.error(request, 'File mamuk.')
			return render(request, 'membro/import.html', context)
		if len(linhas) > MAX_ROWS:
			messages.error(request, f'Linha barak liu ({len(linhas)}). Maximu {MAX_ROWS} ba dala ida.')
			return render(request, 'membro/import.html', context)

		aldeias = {a.code: a for a in Aldeia.objects.select_related('village__administrativepost__municipality') if a.code}
		orgs = {o.code.upper(): o for o in Organizasaun.objects.filter(is_active=True)}
		hasil, erru, forms, eleitoral = [], [], [], set()
		for n, l in enumerate(linhas, start=2):
			l = {k: (v or '').strip() for k, v in l.items() if k}
			ald = aldeias.get(l.get('aldeia_code', ''))
			errs = []
			if not ald:
				errs.append(f'aldeia_code "{l.get("aldeia_code", "")}" la iha')
			org = orgs.get((l.get('organizasaun_code') or '').upper()) if l.get('organizasaun_code') else None
			if l.get('organizasaun_code') and not org:
				errs.append(f'organizasaun_code "{l["organizasaun_code"]}" la iha')
			ele = (l.get('nu_eleitoral') or '').upper()
			if ele and ele in eleitoral:
				errs.append(f'nu. eleitoral {ele} repete iha file')
			eleitoral.add(ele)
			dados = {
				'nome': l.get('nome', ''), 'sex': (l.get('sex') or '').capitalize(), 'date_of_birth': _data(l.get('date_of_birth')),
				'nu_eleitoral': l.get('nu_eleitoral', ''), 'place_of_birth': l.get('place_of_birth', ''), 'marital': l.get('marital', ''),
				'nu_bi': l.get('nu_bi', ''), 'telefone': l.get('telefone', ''), 'address': l.get('address', ''),
				'data_hakbit': _data(l.get('data_hakbit')) if l.get('data_hakbit') else '', 'status': l.get('status') or 'Ativu',
				'organizasaun': org.pk if org else '',
			}
			if ald:
				v = ald.village
				dados.update({'municipality': v.administrativepost.municipality_id, 'post': v.administrativepost_id,
					'village': v.pk, 'aldeia': ald.pk})
			form = MembroForm(dados, user=request.user)
			if not form.is_valid():
				for campo, lista in form.errors.items():
					errs.append(f'{campo}: {"; ".join(lista)}')
			if errs:
				erru.append({'linha': n, 'nome': l.get('nome', ''), 'erru': errs})
			else:
				forms.append(form)
		context.update({'total': len(linhas), 'erru': erru, 'verifika': verifika, 'selesaun': True})
		if erru:
			messages.error(request, f'Import la rai: iha {len(erru)} linha ho erru husi {len(linhas)}. Hadia no tau fali.')
		elif verifika:
			messages.success(request, f'Verifikasaun OK: {len(linhas)} linha loos. Hasai tanda "Verifika deit" atu rai.')
		else:
			with transaction.atomic():
				for f in forms:
					m = f.save(commit=False)
					m.aprovasaun = 'Pendente'
					m.datetime = timezone.now()
					m.user = request.user
					m.save()
					log_historia(request.user, m, 'Importa', f'Importa CSV: {m}')
			notif_aprovador(f'{len(forms)} membru foun husi import CSV hein aprovasaun.', '/membro/aprovasaun/')
			messages.success(request, f'{len(forms)} membru importa ho susesu. Hein aprovasaun.')
			return redirect('membro-list')
	return render(request, 'membro/import.html', context)
