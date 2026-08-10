Locale folder for translations.

Usage:

- Extract messages:

  python manage.py makemessages -l tet -l id -l pt -l en

- Compile translations:

  python manage.py compilemessages

Place translators' `.po` files in `locale/<lang>/LC_MESSAGES/`.
