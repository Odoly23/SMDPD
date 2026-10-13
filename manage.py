#!/usr/bin/env python
"""Utilitas command-line Django untuk SMDPD."""
import os
import sys


def main():
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError("Django la instala. Rai: pip install -r requirements.txt") from exc
	execute_from_command_line(sys.argv)


if __name__ == '__main__':
	main()
