import hmac
import hashlib
from django.conf import settings


def hash_id(value):
	"""HMAC-SHA256 (64 karakter hex) ho xave SECRET_KEY. Uza ba hashid iha URL."""
	return hmac.new(settings.SECRET_KEY.encode(), str(value).encode(), hashlib.sha256).hexdigest()


_FORMULA = ('=', '+', '-', '@', '\t', '\r')


def csv_aman(nilai):
	"""Proteje husi 'CSV/formula injection': testu ne'ebé hahú ho = + - @ sai testu iha Excel/LibreOffice (tau ' iha oin)."""
	if isinstance(nilai, str) and nilai and nilai[0] in _FORMULA:
		return "'" + nilai
	return nilai


class CsvAman:
	"""Pembungkus csv.writer: sanitiza kélula hotu molok hakerek."""

	def __init__(self, destinu):
		import csv
		self._w = csv.writer(destinu)

	def writerow(self, baris):
		return self._w.writerow([csv_aman(c) for c in baris])
