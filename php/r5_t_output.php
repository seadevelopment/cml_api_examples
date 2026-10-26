<?php

/**
 * CML - How to control output (e.g. Y2) of your eStudna device via RPC
 * (PHP equivalent of python/r5_t_output.py)
 */

// ----------------------------------------------------------------------------
// --- Configuration
// ----------------------------------------------------------------------------

// --- Configuration
$user = 'user@example.com';
$password = 'your-password';
$sn = 'XXXXXXXX';   // Serial number of your eSTUDNA


// ----------------------------------------------------------------------------
// --- Code
// ----------------------------------------------------------------------------

function httpPost($url, $data, $header = '')
{
    $options = array
    (
        'http' => array
        (
            'header'  => "Content-Type: application/json\r\nAccept: application/json\r\n" . $header,
            'method'  => 'POST',
            'content' => json_encode($data)
        )
    );
    $context  = stream_context_create($options);
    $result = file_get_contents($url, false, $context);

    if ($result === FALSE)
    {
        throw new Exception('HTTP request failed!');
    }

    return $result;
}

function httpGet($url, $header = '')
{
    $options = array
    (
        'http' => array
        (
            'header'  => "Content-Type: application/json\r\nAccept: application/json\r\n" . $header,
            'method'  => 'GET',
        )
    );
    $context  = stream_context_create($options);
    $result = file_get_contents($url, false, $context);

    if ($result === FALSE)
    {
        throw new Exception('HTTP request failed!');
    }

    return $result;
}

/**
 * Objekt pro pristup k Thingsboardu
 */
class ThingsBoard
{
    public $server =  'https://cml.seapraha.cz';
    public $userToken = null;
    public $customerId = null;

    /**
     * Prihlaseni uzivatele
     */
    public function login($user, $password)
    {
        // Login
        $url = $this->server . '/api/auth/login';
        $result = httpPost($url, array('username' => $user, 'password' => $password));

        $response = json_decode($result);
        $this->userToken = $response->token;    // User token

        // Get customer ID
        $url = $this->server . '/api/auth/user';
        $result = httpGet($url, 'X-Authorization: Bearer ' . $this->userToken);

        $response = json_decode($result);
        $this->customerId = $response->customerId->id; // Customer ID
    }

    /**
     * Vyhledani zarizeni podle nazvu
     */
    public function getDevicesByName($name)
    {
        $url = $this->server . '/api/customer/' . $this->customerId . '/devices?pageSize=100&page=0&textSearch=' . urlencode($name);

        $result = httpGet($url, 'X-Authorization: Bearer ' . $this->userToken);
        $response = json_decode($result);
        if ($response->totalElements < 1)
            throw new Exception('Device SN ' . $name . ' has not been found!');

        return $response->data;         // Return list of devices
    }

    /**
     * Odeslani RPC prikazu zarizeni (twoway - ceka na odpoved zarizeni)
     *
     * POST /api/rpc/twoway/{deviceId}
     * { "method": "state", "params": "Y2 OFF", "timeout": 10000 }
     *
     * timeout - jak dlouho (ms) ceka server na odpoved zarizeni
     */
    public function setDeviceRpc($deviceId, $method, $params, $timeout = 10000)
    {
        $data = array(
            'method'  => $method,
            'params'  => $params,
            'timeout' => $timeout
        );
        $url = $this->server . '/api/rpc/twoway/' . $deviceId;

        return httpPost($url, $data, 'X-Authorization: Bearer ' . $this->userToken);
    }
}

/**
 * Trvale zapnuti vystupu. RPC: {"method": "setY2", "params": 1}
 */
function eStudna_OutputOn($tb, $deviceId, $element)
{
    return $tb->setDeviceRpc($deviceId, 'set' . $element, 1);
}

/**
 * Vypnuti vystupu. RPC: {"method": "state", "params": "Y2 OFF"}
 */
function eStudna_OutputOff($tb, $deviceId, $element)
{
    return $tb->setDeviceRpc($deviceId, 'state', $element . ' OFF');
}

/**
 * Puls - vystup se zapne na $duration sekund a pote se vypne.
 * RPC: {"method": "state", "params": "Y2 PULSE 31"}
 */
function eStudna_OutputPulse($tb, $deviceId, $element, $duration)
{
    return $tb->setDeviceRpc($deviceId, 'state', $element . ' PULSE ' . $duration);
}

/**
 * Reset - vystup se vypne na $duration sekund a pote se zapne.
 * RPC: {"method": "state", "params": "Y2 RESET 35"}
 */
function eStudna_OutputReset($tb, $deviceId, $element, $duration)
{
    return $tb->setDeviceRpc($deviceId, 'state', $element . ' RESET ' . $duration);
}

/**
 * Regulace - prikaz REG s casem v sekundach.
 * RPC: {"method": "state", "params": "Y2 REG 25"}
 */
function eStudna_OutputRegulation($tb, $deviceId, $element, $duration)
{
    return $tb->setDeviceRpc($deviceId, 'state', $element . ' REG ' . $duration);
}


// ----------------------------------------------------------------------------
// --- Main code
// ----------------------------------------------------------------------------

try
{
    // --- ThingsBoard autentizace
    $tb = new ThingsBoard();
    $tb->login($user, $password);
    echo('<pre>Login OK, server: ' . $tb->server . ', user: ' . $user . '</pre>');
    echo('<pre>  customerId: ' . $tb->customerId . '</pre>');
    echo('<pre>  token: ' . substr($tb->userToken, 0, 20) . '...</pre>');

    // --- Nalezeni zarizeni
    $devices = $tb->getDevicesByName('%' . $sn);
    $device = $devices[0];
    $deviceId = $device->id->id;
    echo('<pre>Device: ' . $device->name . ', id: ' . $deviceId . '</pre>');

    // --- Vypnuti
    echo('<pre><b>OFF</b>   -> {"method": "state", "params": "Y2 OFF", "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_OutputOff($tb, $deviceId, 'Y2') . '</pre>');
    sleep(2);

    // --- Zapnuti
    echo('<pre><b>ON</b>    -> {"method": "setY2", "params": 1, "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_OutputOn($tb, $deviceId, 'Y2') . '</pre>');
    sleep(2);

    // --- Impuls 31 s
    echo('<pre><b>PULSE</b> -> {"method": "state", "params": "Y2 PULSE 31", "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_OutputPulse($tb, $deviceId, 'Y2', 31) . '</pre>');
    sleep(2);

    // --- Reset 35 s
    echo('<pre><b>RESET</b> -> {"method": "state", "params": "Y2 RESET 35", "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_OutputReset($tb, $deviceId, 'Y2', 35) . '</pre>');
    sleep(2);

    // --- Regulace 25 s
    echo('<pre><b>REG</b>   -> {"method": "state", "params": "Y2 REG 25", "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_OutputRegulation($tb, $deviceId, 'Y2', 25) . '</pre>');
} catch (Exception $e) {
    echo('<pre>[ EXCEPTION] - ' . $e->getMessage() . '</pre>');
}

?>
