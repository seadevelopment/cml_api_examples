import requests
import json
from time import sleep, time

# ----------------------------------------------------------------------------
# --- Configuration
# ----------------------------------------------------------------------------

# --- Configuration
username = 'user@example.com'
password = 'your-password'
sn = 'XXXXXXXX'   # Serial number of your eSTUDNA


# ----------------------------------------------------------------------------
# --- Code
# ----------------------------------------------------------------------------

def httpPost(url, header={}, params={}, data={}):
    headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      **header
    }
    data=json.dumps(data)
    r = requests.post(url=url, data=data, headers=headers, params=params)
    r.raise_for_status()

    return r.json()


def httpGet(url, header={}, params={}):

    headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      **header
    }
    r = requests.get(url=url, headers=headers, params=params)
    r.raise_for_status()

    return r.json()


class ThingsBoard:
    """
    Objekt pro pristup k Thingsboardu
    """


    def __init__(self):
        self.server = 'https://cml.seapraha.cz'
        self.userToken = None
        self.customerId = None


    def login(self, username: str, password: str):
        """
        Prihlaseni uzivatele (ThingsBoard autentizace)

        1) POST /api/auth/login - Content-Type: application/json
        {
            "username": "user@example.com",
            "password": "heslo"
        }
        odpoved:
        {
            "token": "<JWT access token>",
            "refreshToken": "<JWT refresh token>"
        }

        2) GET /api/auth/user - hlavicka s tokenem:
        X-Authorization: Bearer <JWT access token>
        odpoved (pouzita cast):
        {
            "customerId": {"id": "<customerId>", "entityType": "CUSTOMER"},
            ...
        }

        Token (self.userToken) se pak posila v hlavicce
        "X-Authorization: Bearer <token>" u vsech dalsich volani.
        """
        # Login
        url = f'{self.server}/api/auth/login'
        response = httpPost(url, {}, data={'username': username, 'password': password})
        self.userToken = response["token"]  # User token

        # Get customer ID
        url = f'{self.server}/api/auth/user'
        response = httpGet(url, {'X-Authorization': f"Bearer {self.userToken}"})
        self.customerId = response["customerId"]["id"]  # Customer ID


    def getDevicesByName(self, name: str):
        """
        Vyhledani zarizeni podle nazvu
        """
        url = f'{self.server}/api/customer/{self.customerId}/devices'
        params = {'pageSize': 100, 'page': 0, "textSearch": name}
        response = httpGet(url, {'X-Authorization': f"Bearer {self.userToken}"}, params=params)
        if (response["totalElements"] < 1):
            raise Exception(f"Device SN {name} has not been found!")

        return response["data"]


    def getDeviceKeys(self, deviceId):
        """
        Ziskani seznamu vsech klicu (telemetrie) zarizeni
        """
        url = f'{self.server}/api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries'
        response = httpGet(url, {'X-Authorization': f"Bearer {self.userToken}"})

        return response


    def getDeviceValues(self, deviceId, keys):
        """
        Cteni aktualnich hodnot ze zarizeni
        """
        url = f'{self.server}/api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries'
        params = {'keys': keys}
        response = httpGet(url, {'X-Authorization': f"Bearer {self.userToken}"}, params=params)

        return response


    def getTimeseries(self, deviceId, keys, startTs: int, endTs: int):
        """
        Cteni historickych hodnot ze zarizeni (casy v ms od 1.1.1970)
        """
        url = f'{self.server}/api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries'
        params = {'keys': keys, 'startTs': startTs, 'endTs': endTs}
        response = httpGet(url, {'X-Authorization': f"Bearer {self.userToken}"}, params=params)

        return response


def eStudna_GetDeviceKeys(tb: ThingsBoard, deviceId: str):
    """
    Cteni vsech klicu zarizeni.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)

    GET /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries
    odpoved:
    ["ain1", "ain2", "dout1"]

    Vraci seznam klicu.
    """
    return tb.getDeviceKeys(deviceId)


def eStudna_GetWaterLevel(tb: ThingsBoard, deviceId: str) -> float:
    """
    Cteni aktualni hladiny ve studni.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)

    GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=ain1
    odpoved:
    {
        "ain1": [{"ts": 1698671941000, "value": "2.805"}]
    }
    """
    values = tb.getDeviceValues(deviceId, "ain1")
    return str(values["ain1"][0]["value"])


def eStudna_GetWaterLevelHistory(tb: ThingsBoard, deviceId: str, startTs: int, endTs: int):
    """
    Cteni historie hladiny ve studni.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      startTs  - zacatek intervalu v ms (epoch)
      endTs    - konec intervalu v ms (epoch)

    GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries
        ?keys=ain1&startTs=1698671941000&endTs=1698758341000
    odpoved:
    {
        "ain1": [
            {"ts": 1698758000000, "value": "2.805"},
            {"ts": 1698757000000, "value": "2.801"}
        ]
    }

    Vraci seznam dvojic (hodnota, cas).
    """
    data = tb.getTimeseries(deviceId, "ain1", startTs, endTs)
    return [(str(entry['value']), entry['ts']) for entry in data['ain1']]


if __name__ == "__main__":

    # --- ThingsBoard autentizace
    tb = ThingsBoard()
    tb.login(username, password)
    print(f"Login OK, server: {tb.server}, user: {username}")
    print(f"  customerId: {tb.customerId}")
    print(f"  token: {tb.userToken[:20]}...")

    # --- Nalezeni zarizeni
    device = tb.getDevicesByName(f"%{sn}")[0]
    deviceId = device['id']['id']
    print(f"Device: {device['name']}, id: {deviceId}")

    # --- Vsechny klice zarizeni
    print('\nKEYS -> GET .../keys/timeseries')
    print("Available data keys:", eStudna_GetDeviceKeys(tb, deviceId))

    # --- Aktualni hladina
    print('\nLEVEL -> GET .../values/timeseries?keys=ain1')
    print("ain1 value:", eStudna_GetWaterLevel(tb, deviceId))

    # --- Historie hladiny za poslednich 24 hodin
    endTs = int(time() * 1000)
    startTs = endTs - 24 * 3600 * 1000
    print(f'\nHISTORY -> GET .../values/timeseries?keys=ain1&startTs={startTs}&endTs={endTs}')
    history = eStudna_GetWaterLevelHistory(tb, deviceId, startTs, endTs)
    print("  History (value, ts):", history)

# End of file
