import os
from uuid import uuid4
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from PIL import Image

MAX_PIXEL = 25_000_000
MAX_SISI = 8000
Image.MAX_IMAGE_PIXELS = MAX_PIXEL      # Pillow bloku 'decompression bomb' (error se > 2x)

MAX_IMAGE_MB = 2
IMAGE_EXTS = ('jpg', 'jpeg', 'png')


def upload_foto(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()
	if ext not in IMAGE_EXTS:
		ext = 'jpg'
	return os.path.join('membro_foto', '{}.{}'.format(uuid4().hex, ext))


def upload_logo(instance, filename):
	ext = filename.rsplit('.', 1)[-1].lower()
	if ext not in IMAGE_EXTS:
		ext = 'png'
	return os.path.join('logo_orgaun', '{}.{}'.format(uuid4().hex, ext))


def validate_image_size(image):
	if image.size > MAX_IMAGE_MB * 1024 * 1024:
		raise ValidationError(f'Fotu boot liu {MAX_IMAGE_MB} MB.')


def validate_image_dimensions(image):
	"""Tolak imajen ho dimensaun boot demais (proteje memória server)."""
	try:
		posisaun = image.tell()
	except Exception:
		posisaun = 0
	try:
		with Image.open(image) as im:
			w, h = im.size
	except Exception:
		raise ValidationError("File la'ós imajen JPG/PNG ne'ebé validu.")
	finally:
		try:
			image.seek(posisaun)
		except (AttributeError, OSError, ValueError):
			posisaun = None          # file la bele seek: la importa, validasaun seluk sei hatan
	if w * h > MAX_PIXEL or max(w, h) > MAX_SISI:
		raise ValidationError('Imajen boot liu (maximu 8000 piksel / 25 megapiksel).')


class PrivateStorage(FileSystemStorage):
	"""Storage privadu: pasta husi settings.PRIVATE_MEDIA_ROOT (lee bainhira uza), la iha URL públiku."""
	base_url = None

	@property
	def base_location(self):
		return settings.PRIVATE_MEDIA_ROOT

	@property
	def location(self):
		return os.path.abspath(settings.PRIVATE_MEDIA_ROOT)


def private_storage():
	return PrivateStorage()
