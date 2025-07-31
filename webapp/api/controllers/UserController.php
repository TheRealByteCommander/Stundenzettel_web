<?php
require_once __DIR__ . '/../middleware/AuthMiddleware.php';

class UserController {
    private $db;
    private $authMiddleware;

    public function __construct($db) {
        $this->db = $db;
        $this->authMiddleware = new AuthMiddleware($db);
    }

    public function getUsers($currentUser) {
        $this->authMiddleware->requireAdmin($currentUser);

        try {
            $stmt = $this->db->prepare("SELECT id, email, name, is_admin, created_at FROM users ORDER BY name");
            $stmt->execute();
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);

            // Convert is_admin to boolean
            foreach ($users as &$user) {
                $user['is_admin'] = (bool)$user['is_admin'];
            }

            echo json_encode([
                'success' => true,
                'data' => $users
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Failed to get users']);
        }
    }

    public function updateUser($currentUser, $userId) {
        $this->authMiddleware->requireAdmin($currentUser);

        $input = json_decode(file_get_contents('php://input'), true);

        try {
            // Get current user data
            $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ?");
            $stmt->execute([$userId]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$user) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'User not found']);
                return;
            }

            // Prepare update data
            $updateFields = [];
            $updateValues = [];

            if (isset($input['email']) && $input['email'] !== $user['email']) {
                // Check if email already exists
                $stmt = $this->db->prepare("SELECT COUNT(*) FROM users WHERE email = ? AND id != ?");
                $stmt->execute([$input['email'], $userId]);
                
                if ($stmt->fetchColumn() > 0) {
                    http_response_code(400);
                    echo json_encode(['success' => false, 'message' => 'Email already exists']);
                    return;
                }
                
                $updateFields[] = "email = ?";
                $updateValues[] = $input['email'];
            }

            if (isset($input['name'])) {
                $updateFields[] = "name = ?";
                $updateValues[] = $input['name'];
            }

            if (isset($input['is_admin'])) {
                $updateFields[] = "is_admin = ?";
                $updateValues[] = (bool)$input['is_admin'];
            }

            if (!empty($updateFields)) {
                $updateValues[] = $userId;
                $sql = "UPDATE users SET " . implode(', ', $updateFields) . " WHERE id = ?";
                $stmt = $this->db->prepare($sql);
                $stmt->execute($updateValues);
            }

            echo json_encode([
                'success' => true,
                'message' => 'User updated successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'User update failed']);
        }
    }

    public function deleteUser($currentUser, $userId) {
        $this->authMiddleware->requireAdmin($currentUser);

        // Prevent self-deletion
        if ($userId === $currentUser['id']) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Cannot delete your own account']);
            return;
        }

        try {
            // Get user to delete
            $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ?");
            $stmt->execute([$userId]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$user) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'User not found']);
                return;
            }

            // Check if this is an admin user
            if ($user['is_admin']) {
                // Count total number of admin users
                $stmt = $this->db->prepare("SELECT COUNT(*) FROM users WHERE is_admin = 1");
                $stmt->execute();
                $adminCount = $stmt->fetchColumn();

                if ($adminCount <= 1) {
                    http_response_code(400);
                    echo json_encode([
                        'success' => false, 
                        'message' => 'Cannot delete the last admin user. At least one admin must remain in the system.'
                    ]);
                    return;
                }
            }

            // Delete user (cascading will delete timesheets)
            $stmt = $this->db->prepare("DELETE FROM users WHERE id = ?");
            $stmt->execute([$userId]);

            echo json_encode([
                'success' => true,
                'message' => 'User and associated timesheets deleted successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'User deletion failed']);
        }
    }
}
?>