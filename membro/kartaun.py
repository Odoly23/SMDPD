"""Dadus ba kartaun membru (CR80): pozisaun, nu. militante no logo orgaun."""


def nu_militante(m):
	n = '{0:06d}'.format(m.pk)
	return n[:3] + ' ' + n[3:]


def data_kartaun(m, alokasauns):
	"""alokasauns: lista Alokasaun ativu ba membru ne'e (ho select_related departamentu__organizasaun, organizasaun)."""
	utama = next((a for a in alokasauns if a.pozisaun != 'Membru'), None) or next(iter(alokasauns), None)
	posisaun = utama.pozisaun if utama else 'Membru'
	org = (utama.organizasaun if utama and utama.organizasaun_id else None) or (
		utama.departamentu.organizasaun if utama and utama.departamentu_id else None) or m.organizasaun
	if org:
		posisaun = '{0} - {1}'.format(posisaun, org.code)
	elif utama and utama.unit():
		posisaun = '{0} - {1}'.format(posisaun, utama.unit())
	logo = m.organizasaun.logo.url if m.organizasaun_id and m.organizasaun.logo else None
	return {'posisaun': posisaun, 'nu_militante': nu_militante(m), 'logo_org': logo}
