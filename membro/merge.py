"""Hamutuk membru duplikadu: membru `drop` tama ba `keep` (pozisaun, historia, prezensa, kuota, login) no `drop` hamoos."""
from django.db import transaction
from membro.models import Membro, Alokasaun, Historia

CAMPOS = ['nome', 'sex', 'place_of_birth', 'date_of_birth', 'marital', 'nu_eleitoral', 'nu_bi', 'telefone', 'email', 'image', 'municipality',
	'post', 'village', 'aldeia', 'address', 'organizasaun', 'data_hakbit', 'nivel_edukasaun', 'area_estudu', 'servisu_fatin', 'esperensia',
	'kontribuisaun', 'municipality_orijin']
UNIDADE = ['departamentu_id', 'municipality_id', 'post_id', 'village_id', 'aldeia_id', 'organizasaun_id']


def hamutuk(keep, drop, user):
	"""Return rezumu (dict). Tenke membru diferente."""
	from eventu.models import Prezensa
	from kuota.models import Kuota
	from user.models import UserScope
	from membro.akun import sinkroniza_login
	if keep.pk == drop.pk:
		raise ValueError('Membru hanesan.')
	rez = {'kampu': [], 'pozisaun': 0, 'prezensa': 0, 'kuota': 0}
	with transaction.atomic():
		# 1) kampu ne'ebé mamuk iha `keep` foti husi `drop`
		ele_drop = drop.nu_eleitoral
		if keep.nu_eleitoral in (None, '') and ele_drop:
			drop.nu_eleitoral = None             # liberta unike molok kopia
			drop.save(update_fields=['nu_eleitoral'])
		for k in CAMPOS:
			if k == 'nu_eleitoral':
				if keep.nu_eleitoral in (None, '') and ele_drop:
					keep.nu_eleitoral = ele_drop
					rez['kampu'].append(k)
			elif getattr(keep, k) in (None, '') and getattr(drop, k) not in (None, ''):
				setattr(keep, k, getattr(drop, k))
				rez['kampu'].append(k)
		keep.save()
		# 2) pozisaun: muda ba `keep`, hamoos ne'ebé hanesan ba hanesan
		ada = {(a.nivel, a.pozisaun, a.ativu) + tuple(getattr(a, u) for u in UNIDADE) for a in keep.alokasaun.all()}
		for a in list(drop.alokasaun.all()):
			chave = (a.nivel, a.pozisaun, a.ativu) + tuple(getattr(a, u) for u in UNIDADE)
			if chave in ada:
				a.delete()
			else:
				a.membro = keep
				a.save(update_fields=['membro'])
				ada.add(chave)
				rez['pozisaun'] += 1
		# 3) prezensa no kuota
		ev_keep = set(keep.prezensa.values_list('eventu_id', flat=True))
		for p in list(drop.prezensa.all()):
			if p.eventu_id in ev_keep:
				p.delete()
			else:
				p.membro = keep
				p.save(update_fields=['membro'])
				rez['prezensa'] += 1
		rez['kuota'] = drop.kuota.update(membro=keep) if hasattr(drop, 'kuota') else 0
		# 4) historia
		Historia.objects.filter(membro=drop).update(membro=keep, membro_nome=keep.nome)
		# 5) login
		sd = UserScope.objects.filter(membro=drop).first()
		if sd:
			if UserScope.objects.filter(membro=keep).exists():
				sd.user.is_active = False
				sd.user.save(update_fields=['is_active'])
				sd.membro = None
				sd.save(update_fields=['membro'])
			else:
				sd.membro = keep
				sd.save(update_fields=['membro'])
		nome_drop = str(drop)
		drop_image = drop.image.name if drop.image else None
		keep_image = keep.image.name if keep.image else None
		drop.delete()
		if drop_image and drop_image != keep_image:
			from django.core.files.storage import default_storage
			try:
				default_storage.delete(drop_image)
			except Exception:
				pass
		Historia.objects.create(membro=keep, membro_nome=str(keep), aksaun='Hamutuk', user=user,
			detalhe=f'Hamutuk ho {nome_drop}. Kampu foti: {", ".join(rez["kampu"]) or "-"}; pozisaun: {rez["pozisaun"]}; prezensa: {rez["prezensa"]}; kuota: {rez["kuota"]}')
		sinkroniza_login(keep)
	return rez
