# SMDPD

Sistema Managemen Dadus Membru Partidu PLP (Partidu Libertasaun Popular). Aplikasaun web Django ho interface Tetun.

## Estrutura partidu

| Nivel | Pozisaun |
|---|---|
| **Nasionál** | Presidente, Vice 1–4, Sekretaria, Membru |
| **Departamentu** (iha Estrutura Nasionál) | Presidente Departamentu, Koordenador, Vice 1–4, Membru |
| **Munisipal**, **Postu Administrativu**, **Suku**, **Aldeia** | Koordenador, Vice 1–4, Sekretaria, Membru |
| **Orgaun/Movimentu** | Koordenador, Membru |

Pozisaun hotu (liu Membru) ida de'it ba unidade ida ho estatutu ativu. Konfigurasaun iha `membro/models.py` (`POZISAUN_POR_NIVEL`).

## Peran uzuáriu (`config/roles.py`)

| Peran | Área | Direitu |
|---|---|---|
| Admin | — | Jere uzuáriu, data master (munisipiu, postu, suku, aldeia, departamentu, orgaun/movimentu), historia. La hare data membru. |
| Presidente Nasionál | Nasionál | Hare hotu, **aprova/rejeita/hamoos** membru, aloka pozisaun iha nivel hotu |
| Sekretaria Nasionál | Nasionál | Hare hotu, input/edita membru, aloka pozisaun iha nivel hotu |
| Presidente Departamentu | Departamentu ida | Hare membru departamentu, aloka pozisaun iha departamentu rasik |
| Koordenador Departamentu | Departamentu ida | Hare membru departamentu |
| Koordenador Munisipal / Postu Administrativu / Suku / Aldeia | Área rasik | Input, edita no hare membru iha área rasik |
| Koordenador Orgaun/Movimentu | Orgaun/Movimentu ida | Input, edita no hare membru orgaun/movimentu rasik |

Membru foun ka edita sei hetan estatutu *Pendente* to'o Presidente Nasionál aprova. Presidente simu notifikasaun, no koordenador simu notifikasaun bainhira aprovadu ka rejeitadu.

## Logo entidade iha navbar

Orgaun/Movimentu ida-ida bele iha **logo** rasik (Admin upload iha Data Master → Orgaun/Movimentu, JPG/PNG to'o 2 MB). Bainhira Koordenador Orgaun/Movimentu login, navbar hatudu nia logo no topbar hatudu naran orgaun/movimentu. Struktura Nasionál (no peran seluk) hatudu logo PLP. Orgaun/movimentu sein logo hatudu logo PLP.

## Painel Struktura

Menu **Struktura → Painel** hatudu total membru ba **Entidade** (Orgaun/Movimentu no Struktura), lista **Orgaun/Movimentu** ida-ida (ho paginasaun) no total ba nivel **Struktura** (Nasionál, Departamentu, Munisipal, Postu Administrativu, Suku, Aldeia). `seed_inisial` rejista orgaun/movimentu ne'ebé hatudu iha painel; Admin bele aumenta seluk iha Data Master.

## Mapa Timor-Leste

Halaman **Grafik** hatudu mapa Timor-Leste (Highcharts Maps, lokal iha `main/static/main/js_custom/`) ho total membru tuir munisipiu. Data husi API `report/api/mapa/munisipiu/` ([[xave, total], ...]) tuir área uzuáriu. Munisipiu ida-ida iha *Xave Mapa* (`hckey`, ez. `tl-dl` ba Dili) ne'ebé bele edita iha Data Master → Munisipiu. Atauro seidauk iha iha mapa.

## Dadus wilayah

Munisipiu, Postu Administrativu, Suku no Aldeia foti husi repositóriu **SMKRE** (Diploma Ministerial 31/2026): 14 munisipiu, 71 postu, 472 suku no 2.250 aldeia. File CSV iha `custom/data/`. Importa ho:

```bash
python manage.py import_wilayah --dry-run   # haree deit
python manage.py import_wilayah             # seguru atu la'o dala barak (tuir kódigu)
```

`seed_inisial` mós vota komando ne'e. Munisipiu ne'ebé iha ona sei uza fali tuir naran no atualiza kódigu.

## Apps

- `Core` — projetu Django (settings, urls)
- `config` — peran, dekorador, utilitáriu, permisaun área, seed
- `custom` — data master (Munisipiu → Postu → Suku → Aldeia, Departamentu, Orgaun/Movimentu)
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
python manage.py seed_inisial # peran, wilayah Timor-Leste, orgaun/movimentu, user admin
python manage.py runserver
```

`seed_inisial` kria user `admin`. Se `ADMIN_PASSWORD` mamuk iha `.env`, password aleatóriu sei hatudu ida de'it.

Tuir ida ne'e, tama ho `admin` no rejista postu/suku/aldeia, departamentu no orgaun/movimentu, depois kria uzuáriu ba peran ida-ida.

Database default: SQLite. Ba MySQL, define `DB_ENGINE=mysql` no variavel `DB_*` iha `.env` (instala `mysqlclient`).

## Teste

```bash
python manage.py test
```

## Nota

- Lista membru uza paginasaun server-side (25 per pájina) no esporta CSV tuir filtru no área uzuáriu.
- Tema visuál: layout topbar + navbar + sidebar mobile (`layout.css`), komponen Bootstrapious (`style.default.css`) + `main.css`. Kór tuir logo PLP: verde, kuning no azul.
