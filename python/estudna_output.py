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


    def setDeviceRpc(self, deviceId, method: str, params, timeout: int = 10000):
        """
        Odeslani RPC prikazu zarizeni (twoway - ceka na odpoved zarizeni)

        POST /api/rpc/twoway/{deviceId}
        {
            "method": "setDout1",
            "params": true,
            "timeout": 10000
        }

        timeout - jak dlouho (ms) ceka server na odpoved zarizeni
        """
        data = {"method": method, "params": params, "timeout": timeout}
        url = f'{self.server}/api/rpc/twoway/{deviceId}'
        return httpPost(url, {'X-Authorization': f"Bearer {self.userToken}"}, params={}, data=data)


def eStudna_SetOutput(tb: ThingsBoard, deviceId: str, output: str, state: bool):
    """
    Nastaveni vystupu.

    Parametry:
      tb       - prihlaseny objekt ThingsBoard (tb.login uz byl zavolan)
      deviceId - ID zarizeni (z tb.getDevicesByName)
      output   - "OUT1" nebo "OUT2"
      state    - True = zapnuto, False = vypnuto

    RPC odeslane na POST /api/rpc/twoway/{deviceId}:
    {
        "method": "setDout1",
        "params": true,
        "timeout": 10000
    }
    """
    method = "setDout1" if output == "OUT1" else "setDout2"
    return tb.setDeviceRpc(deviceId, method, state)


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

    # --- Zapnuti
    print('\nON    -> {"method": "setDout1", "params": true, "timeout": 10000}')
    print("  response:", eStudna_SetOutput(tb, deviceId, "OUT1", True))
    sleep(1)

    # --- Vypnuti
    print('\nOFF   -> {"method": "setDout1", "params": false, "timeout": 10000}')
    print("  response:", eStudna_SetOutput(tb, deviceId, "OUT1", False))

# End of file
