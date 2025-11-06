<?php
/**
 * API-Proxy für Backend-URL-Verschleierung
 * 
 * Cyber-Security: Versteckt die echte Proxmox-URL vor dem Frontend.
 * Das Frontend kommuniziert nur mit dieser Proxy-Datei auf All-inkl.com,
 * die dann die Anfragen an das Backend auf Proxmox weiterleitet.
 * 
 * Konfiguration:
 * - BACKEND_URL in .env oder hier direkt setzen
 * - Nur erlaubte Origins werden akzeptiert
 */

header('Content-Type: application/json');

// Konfiguration
$BACKEND_URL = getenv('BACKEND_URL') ?: 'https://proxmox-domain.de:8000';  // Echte Proxmox-URL (NICHT im Frontend!)
$ALLOWED_ORIGINS = [
    'https://app.byte-commander.de',
    'http://localhost:3000',
    'http://localhost:8000'
];

// CORS-Header setzen
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $ALLOWED_ORIGINS)) {
    header("Access-Control-Allow-Origin: $origin");
    header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
    header("Access-Control-Allow-Headers: Content-Type, Authorization");
    header("Access-Control-Allow-Credentials: false");
}

// Preflight-Request behandeln
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Security: Nur POST/GET erlauben
if (!in_array($_SERVER['REQUEST_METHOD'], ['GET', 'POST', 'PUT', 'DELETE'])) {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Security: Referrer-Check
$referer = $_SERVER['HTTP_REFERER'] ?? '';
$is_allowed_referer = false;
foreach ($ALLOWED_ORIGINS as $allowed) {
    if (strpos($referer, $allowed) !== false) {
        $is_allowed_referer = true;
        break;
    }
}

// In Produktion: Referrer-Check aktivieren
if (getenv('ENFORCE_REFERRER_CHECK') === 'true' && !$is_allowed_referer && $referer) {
    http_response_code(403);
    echo json_encode(['error' => 'Access denied: Invalid referer']);
    exit;
}

// API-Pfad aus Request extrahieren
$request_uri = $_SERVER['REQUEST_URI'];
$api_path = str_replace('/api/proxy.php', '', $request_uri);
$api_path = preg_replace('/^\/api\//', '/api/', $api_path);

// Vollständige Backend-URL zusammenbauen
$backend_url = rtrim($BACKEND_URL, '/') . $api_path;

// Query-Parameter hinzufügen
if (!empty($_SERVER['QUERY_STRING'])) {
    $backend_url .= '?' . $_SERVER['QUERY_STRING'];
}

// cURL-Request vorbereiten
$ch = curl_init($backend_url);

// Request-Methode setzen
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD']);

// Headers weiterleiten (wichtig: Authorization-Token)
$headers = [];
foreach (getallheaders() as $name => $value) {
    // Nur wichtige Headers weiterleiten
    if (in_array(strtolower($name), ['authorization', 'content-type', 'accept'])) {
        $headers[] = "$name: $value";
    }
}
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

// POST/PUT-Daten weiterleiten
if (in_array($_SERVER['REQUEST_METHOD'], ['POST', 'PUT'])) {
    $post_data = file_get_contents('php://input');
    curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
}

// Response zurückgeben
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
curl_setopt($ch, CURLOPT_TIMEOUT, 300);  // 5 Minuten für große Uploads

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);

// cURL-Fehler behandeln
if ($response === false) {
    $error = curl_error($ch);
    curl_close($ch);
    http_response_code(500);
    echo json_encode(['error' => 'Proxy error: ' . $error]);
    exit;
}

curl_close($ch);

// HTTP-Status-Code setzen
http_response_code($http_code);

// Content-Type weiterleiten (wichtig für PDF-Downloads)
if ($content_type) {
    header("Content-Type: $content_type");
}

// Response ausgeben
echo $response;
?>

