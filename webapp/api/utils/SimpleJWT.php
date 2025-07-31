<?php
// Simple JWT implementation without external libraries
class SimpleJWT {
    private $secret = 'schmitz-intralogistik-secret-key-2025';
    
    public function encode($payload) {
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $payload = json_encode($payload);
        
        $headerEncoded = $this->base64UrlEncode($header);
        $payloadEncoded = $this->base64UrlEncode($payload);
        
        $signature = hash_hmac('sha256', $headerEncoded . "." . $payloadEncoded, $this->secret, true);
        $signatureEncoded = $this->base64UrlEncode($signature);
        
        return $headerEncoded . "." . $payloadEncoded . "." . $signatureEncoded;
    }
    
    public function decode($jwt) {
        $parts = explode('.', $jwt);
        if (count($parts) !== 3) {
            throw new Exception('Invalid token');
        }
        
        $header = json_decode($this->base64UrlDecode($parts[0]), true);
        $payload = json_decode($this->base64UrlDecode($parts[1]), true);
        $signature = $this->base64UrlDecode($parts[2]);
        
        $expectedSignature = hash_hmac('sha256', $parts[0] . "." . $parts[1], $this->secret, true);
        
        if (!hash_equals($signature, $expectedSignature)) {
            throw new Exception('Invalid signature');
        }
        
        if (isset($payload['exp']) && $payload['exp'] < time()) {
            throw new Exception('Token expired');
        }
        
        return $payload;
    }
    
    private function base64UrlEncode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    private function base64UrlDecode($data) {
        return base64_decode(str_pad(strtr($data, '-_', '+/'), strlen($data) % 4, '=', STR_PAD_RIGHT));
    }
}
?>