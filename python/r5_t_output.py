import requests
import json
from time import sleep

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
        "X-Authorization: Bearer <token>" u vsech dalsich volani,
        vcetne RPC na /api/rpc/twoway/{deviceId}.
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


    def setDeviceOutput(self, deviceId, output: str, value: bool):

        output = "setDout1" if output == "OUT1" else "setDout2"

        data = {"method": output, "params": value}
        url = f'{self.server}/api/rpc/twoway/{deviceId}'
        response = httpPost(url, {'X-Authorization': f"Bearer {self.userToken}"}, params={}, data=data)

        return response

    def setDeviceRpc(self, deviceId, method: str, params, timeout: int = 10000):
        """
        Odeslani RPC prikazu zarizeni (twoway - ceka na odpoved zarizeni)

        POST /api/rpc/twoway/{deviceId}
        {
            "method": "state",
            "params": "Y2 OFF",
            "timeout": 10000
        }

        timeout - jak dlouho (ms) ceka server na odpoved zarizeni
        """
        data = {"method": method, "params": params, "timeout": timeout}
        url = f'{self.server}/api/rpc/twoway/{deviceId}'
        return httpPost(url, {'X-Authorization': f"Bearer {self.userToken}"}, params={}, data=data)


def eStudna_OutputOn(tb: ThingsBoard, deviceId: str, element: str):
    """
    Trvale zapnuti vystupu.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      element  - nazev vystupu, napr. "Y2" (metoda je "set" + element)

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "setY2",
        "params": 1,
        "timeout": 10000
    }
    """
    return tb.setDeviceRpc(deviceId, f"set{element}", 1)


def eStudna_OutputOff(tb: ThingsBoard, deviceId: str, element: str):
    """
    Vypnuti vystupu.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      element  - nazev vystupu, napr. "Y2"

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "state",
        "params": "Y2 OFF",
        "timeout": 10000
    }
    """
    return tb.setDeviceRpc(deviceId, "state", f"{element} OFF")


def eStudna_OutputPulse(tb: ThingsBoard, deviceId: str, element: str, duration: int):
    """
    Puls - vystup se zapne na zadanou dobu a pote se vypne.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      element  - nazev vystupu, napr. "Y2"
      duration - delka impulsu v sekundach

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "state",
        "params": "Y2 PULSE 31",
        "timeout": 10000
    }
    """
    return tb.setDeviceRpc(deviceId, "state", f"{element} PULSE {duration}")


def eStudna_OutputReset(tb: ThingsBoard, deviceId: str, element: str, duration: int):
    """
    Reset - vystup se vypne na zadanou dobu a pote se zapne.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      element  - nazev vystupu, napr. "Y2"
      duration - cas v sekundach

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "state",
        "params": "Y2 RESET 35",
        "timeout": 10000
    }
    """
    return tb.setDeviceRpc(deviceId, "state", f"{element} RESET {duration}")


def eStudna_OutputRegulation(tb: ThingsBoard, deviceId: str, element: str, duration: int):
    """
    Regulace - prikaz REG s casem v sekundach.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      element  - nazev vystupu, napr. "Y2"
      duration - cas v sekundach

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "state",
        "params": "Y2 REG 25",
        "timeout": 10000
    }
    """
    return tb.setDeviceRpc(deviceId, "state", f"{element} REG {duration}")


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

    # --- Vypnuti
    print('\nOFF   -> {"method": "state", "params": "Y2 OFF", "timeout": 10000}')
    print("  response:", eStudna_OutputOff(tb, deviceId, "Y2"))
    sleep(2)

    # --- Zapnuti
    print('\nON    -> {"method": "state", "params": "Y2 ON", "timeout": 10000}')
    print("  response:", eStudna_OutputOn(tb, deviceId, "Y2"))
    sleep(2)

    # --- Impuls 31 s
    print('\nPULSE -> {"method": "state", "params": "Y2 PULSE 31", "timeout": 10000}')
    print("  response:", eStudna_OutputPulse(tb, deviceId, "Y2", 31))
    sleep(2)

    # --- Reset 35 s
    print('\nRESET -> {"method": "state", "params": "Y2 RESET 35", "timeout": 10000}')
    print("  response:", eStudna_OutputReset(tb, deviceId, "Y2", 35))
    sleep(2)

    # --- Regulace 25 s
    print('\nREG   -> {"method": "state", "params": "Y2 REG 25", "timeout": 10000}')
    print("  response:", eStudna_OutputRegulation(tb, deviceId, "Y2", 25))
