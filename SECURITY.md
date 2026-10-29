# Seguransa SMDPD

Dokumentu ne'e rezume proteksaun iha sistema, buat ne'ebé testa ona, no lista ba produksaun. Hatene vulnerabilidade? Haruka relatóriu privadu ba Admin sistema (la publika iha issue públiku).

## Modelu ameasa no proteksaun

| Ameasa | Proteksaun | Tes |
|---|---|---|
| Aksesu la autorizadu | Hotu-hotu **URL** (liu admin Django) husi anónimu = redireciona ba login / 403 API; peran ho `allowed_users`; data tuir **área** (`membro_scope`, `alokasaun_scope`, `eventu_ba`, `anunsiu_ba`, `kuota_scope`) | `tests_audit` crawl URL hotu × peran hotu |
| IDOR | ID iha URL = HMAC-SHA256 (`hashed`) **no** verifika área; objetu fora área = 404 | `tests_audit`, `membro/tests*` |
| Brute force login | 5 tentativa sala/10 min (username+IP, iha database), 2FA mós limitadu | `tests_login_aman` |
| Roubu konta | 2FA TOTP + kódigu rekuperasaun, password ≥ 10 karakter, password foun tenke troka, sesaun idle timeout, sai husi aparelhu hotu, log login | `tests_login_aman` |
| XSS | Autoescape Django iha template hotu (la uza `|safe`/`mark_safe`), input hotu hetan eskapa iha 23 pájina (inklui mensajen flash) | `XssTests` |
| CSRF | Token CSRF iha form hotu; aksaun muda dadus POST deit; cookie HttpOnly+SameSite | `test_csrf_obrigatóriu` |
| SQL injection | ORM deit (la iha `raw()`/`extra()`); parâmetru filtru valida (digit/enum) | bandit |
| **CSV/formula injection** | Esporta CSV hotu uza `CsvAman` (tau `'` iha oin testu ne'ebé hahú ho `= + - @`) | `CsvInjectionTests` |
| Upload perigozu | `ImageField` (Pillow valida kontiñu), ≤ 2 MB, ≤ 8000 px / 25 MP, naran file UUID (la fiar naran husi uzuáriu), SVG/PDF/PHP rejeita | `FotuUploadTests` |
| **Fotu membru** (dadus pesoál) | Rai iha `PRIVATE_MEDIA_ROOT` (la públiku); hatudu deit liu view ho login no área | `FotuUploadTests` |
| Open redirect | `next` login valida host; redirect notifikasaun bloku `//`, `\`, `https:` | `RedirectSeguruTests` |
| Mass assignment | ModelForm ho `fields` eksplísitu; `aprovasaun`, `user`, `hashed` la bele forsa husi POST | `test_mass_assignment...` |
| Konfigurasaun la seguru | `DEBUG` defeitu **False**, laiha xave defeitu iha produksaun (sistema la hahú), HTTPS redirect + HSTS + cookie Secure, header seguransa, `no-store` ba pájina privadu | `KonfigurasaunTests`, `check --deploy` |
| Segredu iha repo | `.env` la tama iha git; tes buka password/xave hardcoded | `test_laiha_xave_iha_repo` |
| Dependénsia | `pip-audit` (la iha vulnerabilidade koñesidu), pustaka JS vendor atualizadu (jQuery 3.7, Bootstrap 4.6, DataTables 1.13) | CI |
| Código | `bandit` (la iha severidade médiu/aas) | CI |

CI (`.github/workflows/ci.yml`) hala'o tes, bandit, pip-audit no `check --deploy` iha push hotu.

## Lista ba produksaun

1. `.env` (la commit): `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY` (aleatóriu ≥ 50 karakter), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://...`, `DJANGO_2FA_WAJIBA=True`. Se hela hodi proxy: `DJANGO_TRUST_PROXY=True`.
2. HTTPS obrigatóriu. Servidór web (nginx/PythonAnywhere) sirve **deit** `/static/` no `/media/` (logo orgaun). **Nunka** esponde `private_media/` (fotu membru) — Django mak hatudu.
3. Database produksaun: MySQL/PostgreSQL ho uzuáriu DB ne'ebé minimu privilejiu; backup regulár (inklui `private_media/`) no tés restore.
4. `python manage.py check --deploy` tenke limpu (aviso HSTS preload mak opsionál).
5. Troka `SECRET_KEY` sei halo ID hashed iha URL sira antigu la valido (favorit/bookmark), maibé la afeta data.
6. Admin: kria konta ho peran minimu; aktiva 2FA; revee **Log Login** regulár; desativa konta ema ne'ebé sai husi pozisaun (sistema halo automátiku ba konta ne'ebé kria husi "Kria login").
7. Atualiza dependénsia regulár (`pip-audit`, `pip install -U -r requirements.txt` no tes).

## Limitasaun koñesidu

- Xave rahasia 2FA rai iha database la kriptografadu (proteje ho akses database); la iha QR code (entrada manuál).
- CSP (`Content-Security-Policy`) seidauk aktiva tamba script inline iha template balu.
- Lokdaun login baseia ba username+IP; atake husi IP barak ba username ida la bloku konta (evita DoS ba uzuáriu loos).
