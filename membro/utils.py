import csv
from django.db.models import Q
from django.http import HttpResponse
from membro.models import Membro, Historia

SNAPSHOT_FIELDS = ['nome', 'sex', 'place_of_birth', 'date_of_birth', 'marital', 'nu_eleitoral', 'nu_bi',
	'telefone', 'email', 'nivel_edukasaun', 'area_estudu', 'servisu_fatin', 'municipality_orijin', 'esperensia', 'kontribuisaun', 'image', 'municipality', 'post', 'village', 'aldeia', 'address', 'organizasaun', 'data_hakbit', 'status']

FILTER_CHOICES = {
	'aprovasaun': ['Pendente', 'Aprovadu', 'Rejeitadu'],
	'status': ['Ativu', 'Inativu', 'Falesidu'],
	'sex': ['Mane', 'Feto'],
}
FILTER_IDS = ['municipality', 'post', 'village', 'aldeia', 'organizasaun']


def snapshot(membro):
	"""Foto kondisaun data membru (label -> teks) ba komparasaun molok/depois edita."""
	data = {}
	for name in SNAPSHOT_FIELDS:
		field = Membro._meta.get_field(name)
		val = getattr(membro, name)
		if name == 'image':
			val = val.name if val else None
		data[str(field.verbose_name)] = '-' if val in (None, '') else str(val)
	return data


def diff_snapshot(old, new):
	lines = [f'{k}: {old[k]} -> {new[k]}' for k in new if old.get(k) != new[k]]
	return '\n'.join(lines)


def log_historia(user, membro, aksaun, detalhe='', nome=None):
	return Historia.objects.create(
		membro=membro, membro_nome=nome or (str(membro) if membro else ''),
		aksaun=aksaun, detalhe=detalhe, user=user)


def apply_filters(qs, params):
	"""Filtru lista membru husi parâmetru GET; valor la validu sei ignora."""
	for key, allowed in FILTER_CHOICES.items():
		val = params.get(key)
		if val in allowed:
			qs = qs.filter(**{key: val})
	for key in FILTER_IDS:
		val = params.get(key)
		if val and val.isdigit():
			qs = qs.filter(**{f'{key}_id': int(val)})
	hakbit = params.get('hakbit')
	if hakbit and hakbit.isdigit():
		qs = qs.filter(data_hakbit__year=int(hakbit))
	q = (params.get('q') or '').strip()
	if q:
		qs = qs.filter(Q(nome__icontains=q) | Q(nu_eleitoral__icontains=q) | Q(nu_bi__icontains=q) | Q(telefone__icontains=q))
	return qs


def export_csv(qs, filename='membru.csv'):
	"""Esporta lista membru ba CSV (UTF-8 ho BOM atu Excel loke loos)."""
	response = HttpResponse(content_type='text/csv; charset=utf-8')
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	response.write('﻿')
	w = csv.writer(response)
	w.writerow(['Nu. Eleitoral', 'Naran', 'Sexu', 'Data Moris', 'Idade', 'Estado Civil', 'Nu. BI', 'Nu. Telemovel',
		'Munisipiu', 'Postu', 'Suku', 'Aldeia', 'Hela Fatin', 'Orgaun/Movimentu', 'Data Hakbit', 'Status', 'Aprovasaun',
		'Email', 'Nivel Estudu', 'Area Estudu', 'Servisu Fatin', 'Munisipiu Orijin'])
	for m in qs.select_related('municipality', 'post', 'village', 'aldeia', 'organizasaun', 'municipality_orijin').iterator():
		w.writerow([m.nu_eleitoral or '', m.nome, m.sex, m.date_of_birth or '', m.age() if m.date_of_birth else '', m.marital or '', m.nu_bi or '', m.telefone or '',
			m.municipality or '', m.post or '', m.village or '', m.aldeia or '', m.address or '', m.organizasaun or '', m.data_hakbit or '',
			m.status, m.aprovasaun, m.email or '', m.nivel_edukasaun or '', m.area_estudu or '', m.servisu_fatin or '', m.municipality_orijin or ''])
	return response
