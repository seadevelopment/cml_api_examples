<?php

/**
 * CML - How to get water level (A1), Y2 value, device keys and level history
 * for your eStudna device (PHP equivalent of python/r5_t_level.py)
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
     * Ziskani seznamu vsech klicu (telemetrie) zarizeni
     */
    public function getDeviceKeys($deviceId)
    {
        $url = $this->server . '/api/plugins/telemetry/DEVICE/' . $deviceId . '/keys/timeseries';

        $result = httpGet($url, 'X-Authorization: Bearer ' . $this->userToken);

        return json_decode($result);
    }

    /**
     * Cteni aktualnich hodnot ze zarizeni
     */
    public function getDeviceValues($deviceId, $keys)
    {
        $url = $this->server . '/api/plugins/telemetry/DEVICE/' . $deviceId . '/values/timeseries?keys=' . $keys;

        $result = httpGet($url, 'X-Authorization: Bearer ' . $this->userToken);

        return json_decode($result);
    }

    /**
     * Cteni historickych hodnot ze zarizeni (casy v ms od 1.1.1970)
     */
    public function getTimeseries($deviceId, $keys, $startTs, $endTs)
    {
        $url = $this->server . '/api/plugins/telemetry/DEVICE/' . $deviceId . '/values/timeseries'
             . '?keys=' . $keys . '&startTs=' . $startTs . '&endTs=' . $endTs;

        $result = httpGet($url, 'X-Authorization: Bearer ' . $this->userToken);

        return json_decode($result);
    }
}

/**
 * Cteni vsech klicu zarizeni
 * Vraci pole klicu.
 */
function eStudna_GetDeviceKeys($tb, $deviceId)
{
    return $tb->getDeviceKeys($deviceId);
}

/**
 * Cteni aktualni hladiny ve studni (klic A1)
 */
function eStudna_GetWaterLevel($tb, $deviceId)
{
    $values = $tb->getDeviceValues($deviceId, 'A1');
    return (string)$values->A1[0]->value;
}

/**
 * Cteni aktualni hodnoty Y2
 */
function eStudna_GetY2($tb, $deviceId)
{
    $values = $tb->getDeviceValues($deviceId, 'Y2');
    return (string)$values->Y2[0]->value;
}

/**
 * Cteni historie hladiny ve studni (klic A1)
 * Vraci pole dvojic array(hodnota, cas).
 */
function eStudna_GetWaterLevelHistory($tb, $deviceId, $startTs, $endTs)
{
    $data = $tb->getTimeseries($deviceId, 'A1', $startTs, $endTs);
    $history = array();
    foreach ($data->A1 as $entry)
    {
        $history[] = array((string)$entry->value, $entry->ts);
    }
    return $history;
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

    // --- Vsechny klice zarizeni
    echo('<pre><b>KEYS</b> -> GET .../keys/timeseries</pre>');
    echo('<pre>Available data keys: ' . implode(', ', eStudna_GetDeviceKeys($tb, $deviceId)) . '</pre>');

    // --- Aktualni hladina
    echo('<pre><b>LEVEL</b> -> GET .../values/timeseries?keys=A1</pre>');
    echo('<pre>A1 value: ' . eStudna_GetWaterLevel($tb, $deviceId) . '</pre>');

    // --- Hodnota Y2
    echo('<pre><b>Y2</b> -> GET .../values/timeseries?keys=Y2</pre>');
    echo('<pre>Y2 value: ' . eStudna_GetY2($tb, $deviceId) . '</pre>');

    // --- Historie hladiny za poslednich 24 hodin
    $endTs = (int)(microtime(true) * 1000);
    $startTs = $endTs - 24 * 3600 * 1000;
    echo('<pre><b>HISTORY</b> -> GET .../values/timeseries?keys=A1&startTs=' . $startTs . '&endTs=' . $endTs . '</pre>');
    $history = eStudna_GetWaterLevelHistory($tb, $deviceId, $startTs, $endTs);
    echo('<pre>History (value, ts):</pre>');
    foreach ($history as $item)
    {
        echo('<pre>  (' . $item[0] . ', ' . $item[1] . ')</pre>');
    }
} catch (Exception $e) {
    echo('<pre>[ EXCEPTION] - ' . $e->getMessage() . '</pre>');
}

?>
