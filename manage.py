#!/usr/bin/env python
"""Utilitas command-line Django ba SMDPD."""
import os
import sys


def main():
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
	if len(sys.argv) > 1 and sys.argv[1] == 'test':
		# Tes uza konfigurasaun dezenvolvimentu (sein HTTPS redirect) ho xave deit ba tes
		os.environ.setdefault('DJANGO_DEBUG', 'True')
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError("Django la instala. Rai: pip install -r requirements.txt") from exc
	execute_from_command_line(sys.argv)


if __name__ == '__main__':
	main()
