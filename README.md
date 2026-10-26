# Příklady práce s CML API (eStudna, GSM-R5-T)

Sada krátkých příkladů v Pythonu a PHP, které ukazují, jak se přes cloud CML (ThingsBoard na `https://cml.seapraha.cz`) přihlásit, najít vaše zařízení, přečíst z něj hodnoty a ovládat jeho výstupy.

Příklady jsou rozdělené podle typu zařízení. Použijte ty, které odpovídají vašemu zařízení, jinak nemusí existovat klíče telemetrie ani RPC příkazy, které skripty očekávají.

| Typ zařízení | Prefix souborů | Sekce |
|---|---|---|
| eStudna, eStudna-DUO, eStudna-SOLAR | `estudna_*` | [eStudna](#estudna-estudna-estudna-duo-estudna-solar) |
| GSM-R5-T, GSM-R5-TI | `r5_t_*` | [GSM-R5-T / GSM-R5-TI](#gsm-r5-t--gsm-r5-ti) |

Všechny soubory jsou samostatné, nemají společný modul. Každý obsahuje vlastní třídu `ThingsBoard` a stejné pomocné funkce pro HTTP.

## Požadavky

- **Python** 3.8+ a knihovna `requests`:
  ```
  pip install requests
  ```
- **PHP** 7+ s povoleným `allow_url_fopen` (skripty používají `file_get_contents` pro HTTP) a rozšířením `openssl` (HTTPS). Skripty vypisují HTML (`<pre>`), takže je lze spustit z příkazové řádky i přes webový server.
- Účet v CML a sériové číslo vašeho zařízení.

## Konfigurace

Na začátku každého souboru je část `Configuration`. Před spuštěním v ní nahraďte zástupné hodnoty:

```python
username = 'user@example.com'    # přihlašovací e-mail do CML
password = 'your-password'       # heslo do CML
sn = 'XXXXXXXX'                  # sériové číslo vašeho zařízení
```

V PHP je to stejné: `$user`, `$password`, `$sn`.

> Do repozitáře nikdy nevkládejte skutečné přihlašovací údaje. Soubory v repozitáři obsahují jen zástupné hodnoty.

---

## eStudna, eStudna-DUO, eStudna-SOLAR

### Soubory

| Soubor | Co dělá |
|---|---|
| `python/estudna_level.py`, `php/estudna_level.php` | Seznam klíčů zařízení, aktuální hladina `ain1`, historie `ain1` za posledních 24 h |
| `python/estudna_output.py`, `php/estudna_output.php` | Zapnutí a vypnutí výstupu `OUT1` (nebo `OUT2`) |

### Spuštění

```
python python/estudna_level.py
python python/estudna_output.py

php php/estudna_level.php
php php/estudna_output.php
```

### Čtení dat

| Účel | Požadavek |
|---|---|
| Seznam všech klíčů zařízení | `GET /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries` |
| Aktuální hodnota | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=ain1` |
| Historie | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=ain1&startTs=<ms>&endTs=<ms>` |

Odpověď:

```json
{"ain1": [{"ts": 1698758000000, "value": "2.805"}]}
```

Historie se vrací jako seznam dvojic `(hodnota, ts)`.

### Ovládání výstupů (RPC)

Funkce `eStudna_OutputOn(tb, deviceId, "OUT1")` a `eStudna_OutputOff(tb, deviceId, "OUT1")` (v PHP stejně, bez typů). Odesílají `POST /api/rpc/twoway/{deviceId}`:

| Akce | `method` | `params` |
|---|---|---|
| Zapnout `OUT1` | `setDout1` | `true` |
| Vypnout `OUT1` | `setDout1` | `false` |
| Zapnout / vypnout `OUT2` | `setDout2` | `true` / `false` |

Tělo požadavku obsahuje i `"timeout": 10000`, například:

```json
{"method": "setDout1", "params": true, "timeout": 10000}
```

> **Pozor:** `estudna_output` skutečně přepíná výstup `OUT1` (zapne, po 1 s vypne). Nespouštějte ho na zařízení, kde je na tomto výstupu připojeno něco, co se nesmí přepnout.

### Ukázkový výstup `estudna_level.py`

Hodnoty jsou ilustrační.

```
Login OK, server: https://cml.seapraha.cz, user: user@example.com
  customerId: 1a2b3c...
  token: eyJhbGciOiJIUzUxMiJ9...
Device: SB821035, id: 4d5e6f...

KEYS -> GET .../keys/timeseries
Available data keys: ['ain1', ...]

LEVEL -> GET .../values/timeseries?keys=ain1
ain1 value: 2.805

HISTORY -> GET .../values/timeseries?keys=ain1&startTs=...&endTs=...
  History (value, ts): [('2.805', 1698758000000), ('2.801', 1698757000000), ...]
```

---

## GSM-R5-T / GSM-R5-TI

### Soubory

| Soubor | Co dělá |
|---|---|
| `python/r5_t_level.py`, `php/r5_t_level.php` | Seznam klíčů zařízení, aktuální hodnota `A1`, hodnota `Y2`, historie `A1` za posledních 24 h |
| `python/r5_t_output.py`, `php/r5_t_output.php` | Ovládání výstupu `Y2` (zapnout, vypnout, puls, reset, regulace) |

### Spuštění

```
python python/r5_t_level.py
python python/r5_t_output.py

php php/r5_t_level.php
php php/r5_t_output.php
```

### Čtení dat

| Účel | Požadavek |
|---|---|
| Seznam všech klíčů zařízení | `GET /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries` |
| Aktuální hodnota | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=A1` |
| Historie | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=A1&startTs=<ms>&endTs=<ms>` |

Odpověď:

```json
{"A1": [{"ts": 1698758000000, "value": "123.4"}]}
```

Historie se vrací jako seznam dvojic `(hodnota, ts)`.

### Ovládání výstupů (RPC)

`POST /api/rpc/twoway/{deviceId}`, element je např. `Y2`:

| Akce | Funkce | `method` | `params` |
|---|---|---|---|
| Trvale zapnout | `eStudna_OutputOn` | `setY2` | `1` |
| Vypnout | `eStudna_OutputOff` | `state` | `"Y2 OFF"` |
| Puls (zapnout na N s, pak vypnout) | `eStudna_OutputPulse` | `state` | `"Y2 PULSE 31"` |
| Reset (vypnout na N s, pak zapnout) | `eStudna_OutputReset` | `state` | `"Y2 RESET 35"` |
| Regulace | `eStudna_OutputRegulation` | `state` | `"Y2 REG 25"` |

Tělo požadavku vždy obsahuje i `"timeout": 10000`.

> **Pozor:** `r5_t_output` skutečně přepíná výstup `Y2` (vypne, zapne, puls 31 s, reset 35 s, regulace 25 s). Nespouštějte ho na zařízení, kde je na tomto výstupu připojeno něco, co se nesmí přepnout.

### Ukázkový výstup `r5_t_level.py`

Hodnoty jsou ilustrační.

```
Login OK, server: https://cml.seapraha.cz, user: user@example.com
  customerId: 1a2b3c...
  token: eyJhbGciOiJIUzUxMiJ9...
Device: GFA26046, id: 4d5e6f...

KEYS -> GET .../keys/timeseries
Available data keys: ['A1', 'Y2', ...]

LEVEL -> GET .../values/timeseries?keys=A1
A1 value: 123.4

Y2 -> GET .../values/timeseries?keys=Y2
Y2 value: 1

HISTORY -> GET .../values/timeseries?keys=A1&startTs=...&endTs=...
  History (value, ts): [('123.4', 1698758000000), ('123.1', 1698757000000), ...]
```

---

## Společné pro všechny příklady

Všechny příklady používají REST API ThingsBoardu. Každý požadavek posílá hlavičky `Content-Type: application/json` a `Accept: application/json`.

### Přihlášení

`POST /api/auth/login` s tělem:

```json
{"username": "user@example.com", "password": "your-password"}
```

Odpověď obsahuje JWT `token`. Ten se u všech dalších požadavků posílá v hlavičce `X-Authorization: Bearer <token>`.

`GET /api/auth/user` vrátí údaje o uživateli, z nich se použije `customerId.id`.

### Nalezení zařízení

`GET /api/customer/{customerId}/devices?pageSize=100&page=0&textSearch=%<SN>`

Vyhledává se podle názvu, takže se před sériové číslo přidává `%`. Pokud zařízení neexistuje (`totalElements < 1`), skript skončí chybou `Device SN ... has not been found!`. ID zařízení je v `data[0].id.id`.

### Časy

`ts`, `startTs` a `endTs` jsou v **milisekundách** od 1. 1. 1970. Hodnota (`value`) je řetězec.

## Řešení problémů

- **HTTP 401 / chyba přihlášení:** zkontrolujte `username` a `password`.
- **`Device SN ... has not been found!`:** zkontrolujte sériové číslo `sn`. Zařízení musí patřit k vašemu účtu.
- **KeyError / prázdná odpověď u `A1`, `Y2` nebo `ain1`:** zařízení tento klíč nemá, nebo používáte příklady pro jiný typ zařízení. Vypište si seznam klíčů a použijte ten správný.
- **PHP: `HTTP request failed!`:** zkontrolujte, že je v `php.ini` zapnuto `allow_url_fopen` a `openssl`.
- **Prázdná historie:** ověřte, že `startTs` a `endTs` jsou v milisekundách a v období, ve kterém zařízení posílalo data.
