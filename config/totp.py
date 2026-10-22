"""TOTP (RFC 6238) sein pustaka externa: HMAC-SHA1, 6 dígitu, 30 segundu."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

PERIODU = 30
DIGITU = 6


def gera_secret():
	return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')


def _kode(secret, step):
	chave = base64.b32decode(secret + '=' * (-len(secret) % 8), casefold=True)
	h = hmac.new(chave, struct.pack('>Q', step), hashlib.sha1).digest()
	o = h[-1] & 0x0F
	return str((struct.unpack('>I', h[o:o + 4])[0] & 0x7FFFFFFF) % (10 ** DIGITU)).zfill(DIGITU)


def kode_agora(secret, t=None):
	return _kode(secret, int((t if t is not None else time.time()) // PERIODU))


def verifika(secret, kode, ultimu_step=0, t=None, janela=1):
	"""Return step ne'ebé loos (> ultimu_step) ka None. Janela ±1 períodu atu aseita relójiu ki'ik la hanesan."""
	kode = (kode or '').strip().replace(' ', '')
	if not (kode.isdigit() and len(kode) == DIGITU):
		return None
	agora = int((t if t is not None else time.time()) // PERIODU)
	for step in range(agora - janela, agora + janela + 1):
		if step > ultimu_step and hmac.compare_digest(_kode(secret, step), kode):
			return step
	return None


def uri(secret, username, emisor='SMDPD PLP'):
	return f'otpauth://totp/{quote(emisor)}:{quote(username)}?secret={secret}&issuer={quote(emisor)}&digits={DIGITU}&period={PERIODU}'


def formata(secret):
	return ' '.join(secret[i:i + 4] for i in range(0, len(secret), 4))
