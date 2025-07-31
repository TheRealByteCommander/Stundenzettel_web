<?php
require_once __DIR__ . '/../utils/SimpleJWT.php';

class AuthMiddleware {
    private $db;
    private $jwt;

    public function __construct($db) {
        $this->db = $db;
        $this->jwt = new SimpleJWT();
    }

    public function requireAuth() {
        $headers = getallheaders();
        $authHeader = isset($headers['Authorization']) ? $headers['Authorization'] : 
                     (isset($headers['authorization']) ? $headers['authorization'] : null);

        if (!$authHeader || !preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
            http_response_code(401);
            echo json_encode(['success' => false, 'message' => 'Authorization header missing']);
            exit();
        }

        $token = $matches[1];

        try {
            $decoded = $this->jwt->decode($token);
            
            // Get user from database
            $stmt = $this->db->prepare("SELECT * FROM users WHERE email = ?");
            $stmt->execute([$decoded['sub']]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$user) {
                http_response_code(401);
                echo json_encode(['success' => false, 'message' => 'User not found']);
                exit();
            }

            return $user;
        } catch (Exception $e) {
            http_response_code(401);
            echo json_encode(['success' => false, 'message' => 'Invalid token']);
            exit();
        }
    }

    public function requireAdmin($user) {
        if (!$user['is_admin']) {
            http_response_code(403);
            echo json_encode(['success' => false, 'message' => 'Admin access required']);
            exit();
        }
    }

    public function createToken($user) {
        $payload = [
            'sub' => $user['email'],
            'iat' => time(),
            'exp' => time() + (24 * 60 * 60) // 24 hours
        ];

        return $this->jwt->encode($payload);
    }
}
?>