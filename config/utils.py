import hmac
import hashlib
from django.conf import settings


def hash_id(value):
	"""HMAC-SHA256 (64 karakter hex) ho xave SECRET_KEY. Uza ba hashid iha URL."""
	return hmac.new(settings.SECRET_KEY.encode(), str(value).encode(), hashlib.sha256).hexdigest()
