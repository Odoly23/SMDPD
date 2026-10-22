import datetime
import difflib
import re
import unicodedata
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from config import roles
from config.decorators import allowed_users
from config.user_utils import c_user_group, membro_scope
from custom.models import Municipality, Organizasaun
from membro.merge import hamutuk
from membro.models import Membro
from membro.utils import log_historia

POR_HALAMAN = 30
MERGE_ROLES = [roles.PRESIDENTE, roles.SEKRETARIA]
KAMPU_UTAMA = [('nu_eleitoral', 'Nu. Eleitoral'), ('date_of_birth', 'Data Moris'), ('aldeia', 'Aldeia / Área'), ('telefone', 'Telemovel'),
	('email', 'Email'), ('image', 'Fotu'), ('nivel_edukasaun', 'Nivel Estudu')]


def _norma(s):
	t = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
	return re.sub(r'[^a-z0-9]', '', t)


def _kompletu_q(campo):
	if campo == 'aldeia':
		return Q(aldeia__isnull=False)
	if campo in ('date_of_birth',):
		return Q(date_of_birth__isnull=False)
	return Q(**{f'{campo}__isnull': False}) & ~Q(**{campo: ''})


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def Kualidade(request):
	"""Kualidade dadus membru: persentajen kompletu, lista ne'ebé falta, no posibilidade duplikadu."""
	group = c_user_group(request.user)
	qs = membro_scope(request.user)
	total = qs.count()
	metrika = []
	for campo, label in KAMPU_UTAMA:
		n = qs.filter(_kompletu_q(campo)).distinct().count()
		metrika.append({'label': label, 'n': n, 'pct': round(100 * n / total) if total else 0})
	kompletu = qs.filter(nu_eleitoral__isnull=False, date_of_birth__isnull=False, aldeia__isnull=False).distinct().count()
	por_mun = []
	for m in Municipality.objects.all():
		t = qs.filter(municipality=m).count()
		if t:
			k = qs.filter(municipality=m, nu_eleitoral__isnull=False, date_of_birth__isnull=False, aldeia__isnull=False).count()
			por_mun.append({'naran': m.name, 'total': t, 'pct': round(100 * k / t)})
	por_org = []
	for o in Organizasaun.objects.filter(is_active=True):
		t = qs.filter(organizasaun=o).count()
		if t:
			k = qs.filter(organizasaun=o, nu_eleitoral__isnull=False, date_of_birth__isnull=False, aldeia__isnull=False).count()
			por_org.append({'naran': o.name, 'total': t, 'pct': round(100 * k / t)})
	falta = qs.filter(Q(nu_eleitoral__isnull=True) | Q(date_of_birth__isnull=True) | Q(aldeia__isnull=True)).distinct().order_by('nome')
	page = Paginator(falta, POR_HALAMAN).get_page(request.GET.get('page'))
	for m in page:
		m.falta = [l for c, l in (('nu_eleitoral', 'Nu. Eleitoral'), ('date_of_birth', 'Data Moris'), ('aldeia', 'Aldeia')) if not getattr(m, c if c != 'aldeia' else 'aldeia_id')]
	duplikadu = _duplikadu(qs) if group in MERGE_ROLES else []
	context = {'group': group, 'total': total, 'kompletu': kompletu, 'pct': round(100 * kompletu / total) if total else 0, 'metrika': metrika,
		'por_mun': por_mun, 'por_org': por_org, 'page': page, 'n_falta': falta.count(), 'duplikadu': duplikadu, 'can_merge': group in MERGE_ROLES,
		'can_edit': group in roles.INPUT_ROLES, 'title': 'Kualidade Dadus', 'legend': 'Kualidade Dadus'}
	return render(request, 'report/kualidade.html', context)


def _duplikadu(qs, limite=40):
	"""Grupu membru ne'ebé posibilidade hanesan: naran hanesan (la sensitivu), ka naran parese ≥ 95%, ka nu. telemovel/BI hanesan."""
	rows = list(qs.values('pk', 'hashed', 'nome', 'telefone', 'nu_bi', 'date_of_birth')[:20000])
	for r in rows:
		r['k'] = _norma(r['nome'])
	grupu = defaultdict(set)
	for chave in ('telefone', 'nu_bi'):
		d = defaultdict(list)
		for r in rows:
			if r[chave]:
				d[r[chave]].append(r['pk'])
		for v, pks in d.items():
			if len(pks) > 1:
				grupu[(chave, v)].update(pks)
	nm = defaultdict(list)
	for r in rows:
		if r['k']:
			nm[r['k']].append(r['pk'])
	for k, pks in nm.items():
		if len(pks) > 1:
			grupu[('naran', k)].update(pks)
	chaves = sorted(nm)
	for i, a in enumerate(chaves):                                  # naran parese (typo)
		for b in chaves[i + 1:i + 40]:
			if abs(len(a) - len(b)) <= 2 and a[:3] == b[:3] and len(a) >= 8 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.9:
				grupu[('parese', a)].update(nm[a] + nm[b])
	por_pk = {r['pk']: r for r in rows}
	hasil, ada = [], set()
	for (sebab, nilai), pks in sorted(grupu.items(), key=lambda x: x[0][0]):
		fz = frozenset(pks)
		if fz in ada:
			continue
		ada.add(fz)
		hasil.append({'sebab': {'telefone': 'Nu. telemovel hanesan', 'nu_bi': 'Nu. BI hanesan', 'naran': 'Naran hanesan', 'parese': 'Naran parese'}[sebab],
			'membru': [por_pk[p] for p in sorted(pks, key=lambda p: por_pk[p]['nome'])][:6]})
		if len(hasil) >= limite:
			break
	return hasil


@login_required
@allowed_users(allowed_roles=MERGE_ROLES)
def MembroHamutuk(request):
	"""Tela hamutuk membru duplikadu: hili ida atu mantein, seluk hamoos (dadus, pozisaun, kuota, prezensa tama ba ida mantein)."""
	group = c_user_group(request.user)
	a = get_object_or_404(membro_scope(request.user), hashed=request.GET.get('a') or request.POST.get('a'))
	b = get_object_or_404(membro_scope(request.user), hashed=request.GET.get('b') or request.POST.get('b'))
	if a.pk == b.pk:
		messages.error(request, 'Hili membru rua ne\'ebé diferente.')
		return redirect('report-kualidade')
	if request.method == 'POST':
		keep_h = request.POST.get('keep')
		if keep_h not in (a.hashed, b.hashed):
			messages.error(request, 'Hili membru ida atu mantein.')
		else:
			keep, drop = (a, b) if keep_h == a.hashed else (b, a)
			rez = hamutuk(keep, drop, request.user)
			messages.success(request, f'Hamutuk ona ba {keep.nome}. Pozisaun: {rez["pozisaun"]}, prezensa: {rez["prezensa"]}, kuota: {rez["kuota"]}.')
			return redirect('membro-detail', keep.hashed)
	campos = [(label, getattr(a, c), getattr(b, c)) for c, label in [
		('nome', 'Naran'), ('nu_eleitoral', 'Nu. Eleitoral'), ('date_of_birth', 'Data Moris'), ('sex', 'Sexu'), ('telefone', 'Telemovel'), ('email', 'Email'),
		('municipality', 'Munisipiu'), ('aldeia', 'Aldeia'), ('organizasaun', 'Orgaun/Movimentu'), ('area_estudu', 'Area Estudu'), ('aprovasaun', 'Aprovasaun')]]
	context = {'group': group, 'a': a, 'b': b, 'campos': campos, 'n_poz': (a.alokasaun.count(), b.alokasaun.count()),
		'title': 'Hamutuk Membru', 'legend': 'Hamutuk Membru'}
	return render(request, 'report/hamutuk.html', context)


@login_required
@allowed_users(allowed_roles=roles.VIEW_ROLES)
def Aniversariu(request):
	"""Membru ne'ebé aniversariu iha loron oin mai (7 ka 30 loron)."""
	group = c_user_group(request.user)
	dias = 30 if request.GET.get('dias') == '30' else 7
	objects = aniversariu_ba(request.user, dias)
	context = {'group': group, 'objects': objects, 'dias': dias, 'title': 'Aniversariu', 'legend': 'Aniversariu'}
	return render(request, 'report/aniversariu.html', context)


def aniversariu_ba(user, dias=7, limite=300):
	"""Lista [{membru, data, idade, loron}] ba aniversariu iha `dias` loron oin mai (inklui ohin)."""
	hoje = timezone.localdate()
	q = Q()
	datas = {}
	for i in range(dias + 1):
		d = hoje + datetime.timedelta(days=i)
		q |= Q(date_of_birth__month=d.month, date_of_birth__day=d.day)
		datas[(d.month, d.day)] = (d, i)
	qs = membro_scope(user).filter(status='Ativu', date_of_birth__isnull=False).filter(q).select_related('municipality', 'organizasaun').distinct()
	out = []
	for m in qs[:limite]:
		d, i = datas[(m.date_of_birth.month, m.date_of_birth.day)]
		out.append({'membru': m, 'data': d, 'idade': d.year - m.date_of_birth.year, 'loron': i})
	out.sort(key=lambda x: (x['loron'], x['membru'].nome))
	return out
