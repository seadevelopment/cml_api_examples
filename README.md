# Příklady práce s eStudnou přes CML API

Sada krátkých příkladů v Pythonu a PHP, které ukazují, jak se přes cloud CML (ThingsBoard na `https://cml.seapraha.cz`) přihlásit, najít vaši eStudnu, přečíst z ní hodnoty a ovládat její výstupy.

## Obsah repozitáře

| Soubor | Co dělá |
|---|---|
| `python/estudna_level.py` | Starší příklad: přečte hladinu (klíč `ain1`) a historii za pevně zadané období |
| `python/estudna_output.py` | Starší příklad: sepne a vypne výstup `OUT1` (RPC `setDout1`) |
| `python/r5_t_level.py` | Nový příklad: seznam klíčů zařízení, aktuální hladina `A1`, hodnota `Y2`, historie `A1` za posledních 24 h |
| `python/r5_t_output.py` | Nový příklad: ovládání výstupu `Y2` (zapnout, vypnout, puls, reset, regulace) |
| `php/estudna_level.php` | PHP verze `estudna_level` (aktuální hladina `ain1`) |
| `php/estudna_output.php` | PHP verze `estudna_output` (výstup `OUT1`) |
| `php/r5_t_level.php` | PHP verze `r5_t_level.py` |
| `php/r5_t_output.php` | PHP verze `r5_t_output.py` |

### Pro která zařízení jsou příklady určeny

| Prefix souboru | Podporovaná zařízení |
|---|---|
| `estudna_*` | eStudna, eStudna-DUO, eStudna-SOLAR |
| `r5_t_*` | GSM-R5-T, GSM-R5-TI |

Používejte příklady odpovídající vašemu zařízení, jinak nemusí existovat klíče telemetrie ani RPC příkazy, které skripty očekávají.

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
sn = 'XXXXXXXX'                  # sériové číslo vaší eStudny
```

V PHP je to stejné: `$user`, `$password`, `$sn`.

> Do repozitáře nikdy nevkládejte skutečné přihlašovací údaje. Soubory v repozitáři obsahují jen zástupné hodnoty.

## Spuštění

Python:

```
python python/r5_t_level.py
python python/r5_t_output.py
```

PHP z příkazové řádky, nebo umístěním na webový server:

```
php php/r5_t_level.php
php php/r5_t_output.php
```

## Ukázkový výstup

`r5_t_level.py` (hodnoty jsou ilustrační):

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

`r5_t_output.py` po každém kroku vypíše odpověď zařízení.

> **Pozor:** `r5_t_output` skutečně přepíná výstup `Y2` (vypne, zapne, puls 31 s, reset 35 s, regulace 25 s). Nespouštějte ho na zařízení, kde je na tomto výstupu připojeno něco, co se nesmí přepnout.

## Jak to funguje

Všechny příklady používají REST API ThingsBoardu. Každý požadavek posílá hlavičky `Content-Type: application/json` a `Accept: application/json`.

### 1. Přihlášení

`POST /api/auth/login` s tělem:

```json
{"username": "user@example.com", "password": "your-password"}
```

Odpověď obsahuje JWT `token`. Ten se u všech dalších požadavků posílá v hlavičce `X-Authorization: Bearer <token>`.

`GET /api/auth/user` vrátí údaje o uživateli, z nich se použije `customerId.id`.

### 2. Nalezení zařízení

`GET /api/customer/{customerId}/devices?pageSize=100&page=0&textSearch=%<SN>`

Vyhledává se podle názvu, takže se před sériové číslo přidává `%`. Pokud zařízení neexistuje (`totalElements < 1`), skript skončí chybou `Device SN ... has not been found!`. ID zařízení je v `data[0].id.id`.

### 3. Čtení dat (telemetrie)

| Účel | Požadavek |
|---|---|
| Seznam všech klíčů zařízení | `GET /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries` |
| Aktuální hodnota | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=A1` |
| Historie | `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=A1&startTs=<ms>&endTs=<ms>` |

Odpověď na hodnoty má tvar:

```json
{"A1": [{"ts": 1698758000000, "value": "123.4"}]}
```

- `ts` je čas v **milisekundách** od 1. 1. 1970. Pozor, `startTs` i `endTs` musí být v milisekundách.
- `value` je řetězec.
- Historie se v `r5_t_level` vrací jako seznam dvojic `(hodnota, ts)`.
- Starší příklady používají klíč `ain1`, novější (`r5_t_*`) klíč `A1`. Které klíče vaše zařízení má, zjistíte voláním seznamu klíčů.

### 4. Ovládání výstupů (RPC)

`POST /api/rpc/twoway/{deviceId}`. Server čeká na odpověď zařízení, jak dlouho určuje `timeout` v ms (výchozí 10000).

Starší příklady (`estudna_output`):

```json
{"method": "setDout1", "params": true}
```

Novější příklady (`r5_t_output`), element je např. `Y2`:

| Akce | `method` | `params` |
|---|---|---|
| Trvale zapnout | `setY2` | `1` |
| Vypnout | `state` | `"Y2 OFF"` |
| Puls (zapnout na N s, pak vypnout) | `state` | `"Y2 PULSE 31"` |
| Reset (vypnout na N s, pak zapnout) | `state` | `"Y2 RESET 35"` |
| Regulace | `state` | `"Y2 REG 25"` |

Tělo požadavku vždy obsahuje i `"timeout": 10000`.

## Řešení problémů

- **HTTP 401 / chyba přihlášení:** zkontrolujte `username` a `password`.
- **`Device SN ... has not been found!`:** zkontrolujte sériové číslo `sn`. Zařízení musí patřit k vašemu účtu.
- **KeyError / prázdná odpověď u `A1`, `Y2` nebo `ain1`:** zařízení tento klíč nemá. Vypište si seznam klíčů a použijte ten správný.
- **PHP: `HTTP request failed!`:** zkontrolujte, že je v `php.ini` zapnuto `allow_url_fopen` a `openssl`.
- **Prázdná historie:** ověřte, že `startTs` a `endTs` jsou v milisekundách a v období, ve kterém zařízení posílalo data.
