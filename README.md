# SMDPD

Sistema Managemen Dadus Membru Partidu PLP (Partidu Libertasaun Popular). Aplikasaun web Django ho interface Tetun.

## Estrutura partidu

| Nivel | Pozisaun |
|---|---|
| **Nasionál** | Presidente, Vice 1–4, Sekretaria, Membru |
| **Departamentu** (iha Estrutura Nasionál) | Presidente Departamentu, Koordenador, Vice 1–4, Membru |
| **Munisipal**, **Postu Administrativu**, **Suku**, **Aldeia** | Koordenador, Vice 1–4, Sekretaria, Membru |
| **Orgaun/Movimentu** (ez. SEE) | Presidente, Vice 1–8, Sekretaria, Koordenador, Membru. Orgaun/movimentu mós bele iha **departamentu** rasik no **filiál iha munisipiu** (pozisaun orgaun + munisipiu) |

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
| Presidente Orgaun/Movimentu | Orgaun/Movimentu ida | Hare membru orgaun, aloka pozisaun iha orgaun no nia departamentu, kria login ba Vice/Sekretaria/Koordenador |
| Sekretaria / Koordenador Orgaun/Movimentu | Orgaun/Movimentu ida | Input, edita no hare membru orgaun rasik |
| Vice Orgaun/Movimentu | Orgaun/Movimentu ida | Hare membru orgaun rasik |

Membru foun ka edita sei hetan estatutu *Pendente* to'o Presidente Nasionál aprova. Presidente simu notifikasaun, no koordenador simu notifikasaun bainhira aprovadu ka rejeitadu.

## Login ba pozisaun (membru ordináriu la login)

Membru ordináriu **la iha login**. Deit pozisaun ne'ebé iha ona peran bele hetan konta: Presidente/Sekretaria Nasionál, Presidente/Koordenador Departamentu, Koordenador Munisipal/Postu/Suku/Aldeia no Presidente/Vice/Sekretaria/Koordenador Orgaun/Movimentu. Iha **Struktura** → botaun **Kria** (login) bainhira membru aprovadu no ativu; username = nu. eleitoral, password aleatóriu hatudu dala ida deit. Konta sai ativu/la ativu automátiku tuir pozisaun (hamoos pozisaun ka membru falesidu → konta desativa). Presidente Orgaun la bele kria login ba Presidente Orgaun (Presidente Nasionál mak halo); deit Presidente Nasionál bele kria login nasionál.

## Importa Database SEE-PLP (Excel) no Rekursu Intelektual

```bash
python manage.py import_see /dalan/Database_SEE-PLP_2026.xlsx --dry-run   # haree rezultadu no avizu deit
python manage.py import_see /dalan/Database_SEE-PLP_2026.xlsx             # membru foun = Pendente (uza --aprova atu Aprovadu)
```

- Aba **Form Responses 1** = fonte prinsipál: membru, departamentu, pozisaun (Presidente, Vice 1–8, Koordenador, Membru) no estrutura (nasionál ka munisipiu). Naran pozisaun no departamentu ne'ebé la hanesan (ex. *Vise 3*, *Vice Koordenador II*, *Asunto/Asuntu Finansas*) hetan normaliza; pozisaun ida ne'ebé okupadu ona sai *Membru* no avizu hatudu iha relatóriu.
- Aba **Sheet1** (formulariu rekursu intelektual): naran iha aba ne'e la hanesan ho liña dadus nian, nune'e liña *hatán* ba membru liu husi nu. telemovel (ka email, ka área+nivel úniku); ne'ebé la hatán la importa no hatudu iha avizu.
- Membru bele la iha nu. eleitoral/data moris/área: marka **!** (dadus seidauk kompletu) no formuláriu edita obriga kompleta.
- Seguru atu la'o dala barak; la sobu-hakerek dadus ne'ebé edita ona. **File Excel ho dadus pesoál la tama iha repositóriu.**

**Relatoriu → Rekursu** (`/report/rekursu/`) = formulariu *Baze de Dadus ba Rekursus Intelektuais* (Orgaun Konsultivu/SEE): lista alfabétika ho Area Estudu, Nivel, Esperensia, Kontribuisaun, Munisipiu Orijin/Rezidensia, Nu. Kontaktu no Email, bele **imprime** (A4 landscape, títulu no assinatura bele edita molok imprime) no **esporta CSV**. Títulu no sede orgaun hanesan iha Data Master → Orgaun/Movimentu.

## Fitur ba partidu boot

- **Anunsiu** (`/anunsiu/`): komunikadu husi lideransa ba PLP tomak, munisipiu, orgaun/movimentu ka departamentu. Kria: Presidente/Sekretaria Nasionál (hotu), Presidente Orgaun, Presidente Departamentu no Koordenador Munisipal (unidade rasik). Uzuáriu iha audiens simu notifikasaun; anunsiu hatudu iha Varanda; bele marka *importante* no iha data validu.
- **Eventu no Prezensa** (`/eventu/`): reuniaun, formasaun, kongresu, kampaña. Área eventu = área ema ne'ebé kria; eventu nasionál hare hotu. **Foti prezensa** ho lista (buka + paginasaun, Prezente/Lisensa/Falta, tanda hotu), **prezensa rápidu** ho nu. eleitoral, esporta CSV; istória prezensa hatudu iha detalha membru.
- **Kuota membru** (`/kuota/`): rejistu kuota (USD) ba tinan ida, rezumu (total, % selu, tuir munisipiu no orgaun) no lista membru ne'ebé seidauk selu (esporta CSV).
- **Kualidade Dadus** (`/report/kualidade/`): persentajen dadus kompletu tuir kampu/munisipiu/orgaun, lista membru ne'ebé falta dadus no **deteta duplikadu** (naran hanesan/parese, nu. telemovel/BI hanesan). Presidente/Sekretaria Nasionál bele **hamutuk** membru duplikadu (pozisaun, prezensa, kuota, historia no login tama ba membru ne'ebé mantein).
- **Aniversariu** (`/report/aniversariu/`) no widget iha Varanda; grafik **rejistu foun 12 fulan ikus**.
- **Seguransa**: password foun (husi Admin ka husi "Kria login") tenke troka bainhira login; tentativa login sala limitadu (5 dala / 10 minutu ba username + IP).

## Login seguru

| Proteksaun | Detallu |
|---|---|
| Password | minimu 10 karakter, la bele komún/numéricu deit; password foun (husi Admin ka "Kria login") **tenke troka** iha login uluk |
| Lokdaun | 5 tentativa sala iha 10 minutu ba kombinasaun *username + IP* → bloku 10 minutu. Rai iha **database** (seguru ba worker barak) |
| **2FA (TOTP)** | Aplikasaun authenticator (Google/Microsoft Authenticator, Authy, FreeOTP) liu husi menu *Seguransa (2FA)*. Kódigu ida uza dala ida deit (anti-replay), ho 8 **kódigu rekuperasaun**. Obrigatóriu ba Admin/Presidente/Sekretaria Nasionál se `DJANGO_2FA_WAJIBA=True` |
| Log login | Admin hare **Log Login** (susesu, sala, bloku, 2FA sala, sai, reset ho IP no browser). Uzuáriu hare "Login molok ne'e" iha menu konta |
| Sesaun | sai automátiku (`SESSION_IDLE_MINUTES`) no bainhira taka browser; cookie HttpOnly + SameSite; **Sai husi aparelhu hotu**; troka password hamoos sesaun seluk |
| Admin | **Reset password** (password temporáriu dala ida deit) no **Reset 2FA** ba uzuáriu ne'ebé perde telemovel; la bele reset ba an rasik |
| Header/HTTPS | `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` ba pájina privadu; iha produksaun: HTTPS redirect, HSTS, cookie `Secure`; URL admin Django bele muda |

Aplikasaun *authenticator* ho kódigu manuál (la iha QR): tau xave ne'ebé hatudu iha pájina 2FA. Se uza proxy/nginx ho HTTPS, define `DJANGO_TRUST_PROXY=True` atu IP loos no HTTPS hetan rekoñese. Verifika konfigurasaun ho `DJANGO_DEBUG=False python manage.py check --deploy`.

## Seguransa kódigu

Audit seguransa tomak (otorizasaun hotu-hotu URL, XSS, CSV injection, upload, fotu privadu, redirect, CSRF, konfigurasaun) iha `config/tests_audit.py`, `bandit`/`pip-audit` iha CI. Detallu, lista produksaun no limitasaun: **[SECURITY.md](SECURITY.md)**. `DEBUG` defeitu **la aktivu**: ba dezenvolvimentu kopia `.env.example` ba `.env` (`DJANGO_DEBUG=True`). Fotu membru rai iha `private_media/` (la públiku) no hatudu liu view ho login no área.

## Fitur seluk

- **Kartaun Membru** (ID card imprime), **Importa CSV** (verifika uluk, rai tudu ka laiha), esporta CSV.
- Menu Struktura hatudu deit nivel relevante ba peran; tabela membru sai kartu iha telemovel; modal konfirmasaun; alerta otomátiku; botaun fila ba leten.

## Logo entidade iha navbar

Orgaun/Movimentu ida-ida bele iha **logo** rasik (Admin upload iha Data Master → Orgaun/Movimentu, JPG/PNG to'o 2 MB). Bainhira peran orgaun/movimentu (ka departamentu husi orgaun) login, navbar hatudu nia logo no topbar hatudu naran orgaun/movimentu. Struktura Nasionál (no peran seluk) hatudu logo PLP. Orgaun/movimentu sein logo hatudu logo PLP.

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
cp .env.example .env          # DJANGO_DEBUG=True (dev); iha produksaun: DEBUG=False + DJANGO_SECRET_KEY
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
