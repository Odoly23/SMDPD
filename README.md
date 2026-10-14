# SMDPD

Sistema Managemen Dadus Membru Partidu PLP (Partidu Libertasaun Popular). Aplikasaun web Django ho interface Tetun.

## Estrutura partidu

| Nivel | Pozisaun |
|---|---|
| **Nasionál** | Presidente, Vice 1–4, Sekretaria, Membru |
| **Departamentu** (iha Estrutura Nasionál) | Presidente Departamentu, Koordenador, Vice 1–4, Membru |
| **Munisipiu**, **Suku**, **Aldeia** | Koordenador, Vice 1–4, Sekretaria, Membru |
| **Organizasaun** | Koordenador, Membru |

Pozisaun hotu (liu Membru) ida de'it ba unidade ida ho estatutu ativu. Konfigurasaun iha `membro/models.py` (`POZISAUN_POR_NIVEL`).

## Peran uzuáriu (`config/roles.py`)

| Peran | Área | Direitu |
|---|---|---|
| Admin | — | Jere uzuáriu, data master (munisipiu, postu, suku, aldeia, departamentu, organizasaun), historia. La hare data membru. |
| Presidente Nasionál | Nasionál | Hare hotu, **aprova/rejeita/hamoos** membru, aloka pozisaun iha nivel hotu |
| Sekretaria Nasionál | Nasionál | Hare hotu, input/edita membru, aloka pozisaun iha nivel hotu |
| Presidente Departamentu | Departamentu ida | Hare membru departamentu, aloka pozisaun iha departamentu rasik |
| Koordenador Departamentu | Departamentu ida | Hare membru departamentu |
| Koordenador Munisipiu / Suku / Aldeia | Área rasik | Input, edita no hare membru iha área rasik |
| Koordenador Organizasaun | Organizasaun ida | Input, edita no hare membru organizasaun rasik |

Membru foun ka edita sei hetan estatutu *Pendente* to'o Presidente Nasionál aprova. Presidente simu notifikasaun, no koordenador simu notifikasaun bainhira aprovadu ka rejeitadu.

## Apps

- `Core` — projetu Django (settings, urls)
- `config` — peran, dekorador, utilitáriu, permisaun área, seed
- `custom` — data master (Munisipiu → Postu → Suku → Aldeia, Departamentu, Organizasaun)
- `membro` — membru, pozisaun iha struktura (`Alokasaun`), historia mudansa, aprovasaun
- `user` — uzuáriu no área ida-ida (`UserScope`)
- `notif` — notifikasaun
- `report` — relatoriu, grafik no API
- `main` — layout, login, dashboard, static (tema Bootstrapious)

## Instala

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # troka DJANGO_SECRET_KEY
python manage.py migrate
python manage.py seed_inisial # peran, munisipiu Timor-Leste, user admin
python manage.py runserver
```

`seed_inisial` kria user `admin`. Se `ADMIN_PASSWORD` mamuk iha `.env`, password aleatóriu sei hatudu ida de'it.

Tuir ida ne'e, tama ho `admin` no rejista postu/suku/aldeia, departamentu no organizasaun, depois kria uzuáriu ba peran ida-ida.

Database default: SQLite. Ba MySQL, define `DB_ENGINE=mysql` no variavel `DB_*` iha `.env` (instala `mysqlclient`).

## Teste

```bash
python manage.py test
```

## Nota

- Lista membru uza paginasaun server-side (25 per pájina) no esporta CSV tuir filtru no área uzuáriu.
- Tema visuál: `main/static/main/css/style.default.css` (Bootstrapious Dashboard) + `main.css`.
