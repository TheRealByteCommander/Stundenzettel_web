<?php
require_once __DIR__ . '/../middleware/AuthMiddleware.php';

class AdminController {
    private $db;
    private $authMiddleware;

    public function __construct($db) {
        $this->db = $db;
        $this->authMiddleware = new AuthMiddleware($db);
    }

    public function saveSmtpConfig($currentUser) {
        $this->authMiddleware->requireAdmin($currentUser);

        $input = json_decode(file_get_contents('php://input'), true);

        if (!isset($input['smtp_server']) || !isset($input['smtp_username']) || !isset($input['admin_email'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'SMTP server, username and admin email required']);
            return;
        }

        try {
            // Delete existing config
            $stmt = $this->db->prepare("DELETE FROM smtp_config");
            $stmt->execute();

            // Create new config
            $stmt = $this->db->prepare("
                INSERT INTO smtp_config (id, smtp_server, smtp_port, smtp_username, smtp_password, admin_email) 
                VALUES (?, ?, ?, ?, ?, ?)
            ");

            $configId = $this->generateUUID();
            $smtpPort = isset($input['smtp_port']) ? (int)$input['smtp_port'] : 587;

            $stmt->execute([
                $configId,
                $input['smtp_server'],
                $smtpPort,
                $input['smtp_username'],
                $input['smtp_password'],
                $input['admin_email']
            ]);

            echo json_encode([
                'success' => true,
                'message' => 'SMTP configuration updated successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'SMTP configuration update failed']);
        }
    }

    public function getSmtpConfig($currentUser) {
        $this->authMiddleware->requireAdmin($currentUser);

        try {
            $stmt = $this->db->prepare("SELECT smtp_server, smtp_port, smtp_username, admin_email FROM smtp_config ORDER BY created_at DESC LIMIT 1");
            $stmt->execute();
            $config = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$config) {
                echo json_encode(['success' => true, 'data' => null]);
                return;
            }

            echo json_encode([
                'success' => true,
                'data' => $config
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Failed to get SMTP configuration']);
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