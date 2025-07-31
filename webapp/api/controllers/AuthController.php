<?php
require_once __DIR__ . '/../middleware/AuthMiddleware.php';

class AuthController {
    private $db;
    private $authMiddleware;

    public function __construct($db) {
        $this->db = $db;
        $this->authMiddleware = new AuthMiddleware($db);
    }

    public function login() {
        $input = json_decode(file_get_contents('php://input'), true);

        if (!isset($input['email']) || !isset($input['password'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Email and password required']);
            return;
        }

        try {
            $stmt = $this->db->prepare("SELECT * FROM users WHERE email = ?");
            $stmt->execute([$input['email']]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$user || !password_verify($input['password'], $user['password_hash'])) {
                http_response_code(401);
                echo json_encode(['success' => false, 'message' => 'Invalid credentials']);
                return;
            }

            $token = $this->authMiddleware->createToken($user);

            echo json_encode([
                'success' => true,
                'data' => [
                    'access_token' => $token,
                    'user' => [
                        'id' => $user['id'],
                        'email' => $user['email'],
                        'name' => $user['name'],
                        'is_admin' => (bool)$user['is_admin']
                    ]
                ]
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Login failed']);
        }
    }

    public function register($currentUser) {
        $this->authMiddleware->requireAdmin($currentUser);

        $input = json_decode(file_get_contents('php://input'), true);

        if (!isset($input['email']) || !isset($input['name']) || !isset($input['password'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Email, name and password required']);
            return;
        }

        try {
            // Check if user exists
            $stmt = $this->db->prepare("SELECT COUNT(*) FROM users WHERE email = ?");
            $stmt->execute([$input['email']]);
            
            if ($stmt->fetchColumn() > 0) {
                http_response_code(400);
                echo json_encode(['success' => false, 'message' => 'Email already exists']);
                return;
            }

            // Create user
            $stmt = $this->db->prepare("
                INSERT INTO users (id, email, name, password_hash, is_admin) 
                VALUES (?, ?, ?, ?, ?)
            ");

            $userId = $this->generateUUID();
            $passwordHash = password_hash($input['password'], PASSWORD_DEFAULT);
            $isAdmin = isset($input['is_admin']) ? (bool)$input['is_admin'] : false;

            $stmt->execute([
                $userId,
                $input['email'],
                $input['name'],
                $passwordHash,
                $isAdmin
            ]);

            echo json_encode([
                'success' => true,
                'data' => ['user_id' => $userId],
                'message' => 'User created successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'User creation failed']);
        }
    }

    public function me($user) {
        echo json_encode([
            'success' => true,
            'data' => [
                'id' => $user['id'],
                'email' => $user['email'],
                'name' => $user['name'],
                'is_admin' => (bool)$user['is_admin']
            ]
        ]);
    }

    public function changePassword($user) {
        $input = json_decode(file_get_contents('php://input'), true);

        if (!isset($input['current_password']) || !isset($input['new_password'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Current and new password required']);
            return;
        }

        try {
            // Verify current password
            if (!password_verify($input['current_password'], $user['password_hash'])) {
                http_response_code(400);
                echo json_encode(['success' => false, 'message' => 'Current password is incorrect']);
                return;
            }

            // Update password
            $stmt = $this->db->prepare("UPDATE users SET password_hash = ? WHERE id = ?");
            $newPasswordHash = password_hash($input['new_password'], PASSWORD_DEFAULT);
            $stmt->execute([$newPasswordHash, $user['id']]);

            echo json_encode([
                'success' => true,
                'message' => 'Password changed successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Password change failed']);
        }
    }

    private function generateUUID() {
        return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
    }
}
?>