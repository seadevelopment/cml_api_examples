<?php

/**
 * CML - How to control output (OUT1/OUT2) of your eStudna device via RPC
 * (PHP equivalent of python/estudna_output.py)
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
     * { "method": "setDout1", "params": true, "timeout": 10000 }
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
 * Nastaveni vystupu ("OUT1" nebo "OUT2"), $state: true = zapnuto, false = vypnuto
 * RPC: {"method": "setDout1", "params": true}
 */
function eStudna_SetOutput($tb, $deviceId, $output, $state)
{
    $method = ($output == 'OUT1') ? 'setDout1' : 'setDout2';
    return $tb->setDeviceRpc($deviceId, $method, $state);
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

    // --- Zapnuti
    echo('<pre><b>ON</b>  -> {"method": "setDout1", "params": true, "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_SetOutput($tb, $deviceId, 'OUT1', true) . '</pre>');
    sleep(1);

    // --- Vypnuti
    echo('<pre><b>OFF</b> -> {"method": "setDout1", "params": false, "timeout": 10000}</pre>');
    echo('<pre>  response: ' . eStudna_SetOutput($tb, $deviceId, 'OUT1', false) . '</pre>');
} catch (Exception $e) {
    echo('<pre>[ EXCEPTION] - ' . $e->getMessage() . '</pre>');
}

?>
