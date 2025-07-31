<?php
require_once __DIR__ . '/../middleware/AuthMiddleware.php';
require_once __DIR__ . '/../utils/PDFGenerator.php';
require_once __DIR__ . '/../utils/EmailService.php';

class TimesheetController {
    private $db;
    private $authMiddleware;

    public function __construct($db) {
        $this->db = $db;
        $this->authMiddleware = new AuthMiddleware($db);
    }

    public function getTimesheets($currentUser) {
        try {
            if ($currentUser['is_admin']) {
                $stmt = $this->db->prepare("SELECT * FROM timesheets ORDER BY created_at DESC");
                $stmt->execute();
            } else {
                $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE user_id = ? ORDER BY created_at DESC");
                $stmt->execute([$currentUser['id']]);
            }

            $timesheets = $stmt->fetchAll(PDO::FETCH_ASSOC);

            // Parse JSON entries and format dates
            foreach ($timesheets as &$timesheet) {
                $timesheet['entries'] = json_decode($timesheet['entries'], true);
            }

            echo json_encode([
                'success' => true,
                'data' => $timesheets
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Failed to get timesheets']);
        }
    }

    public function createTimesheet($currentUser) {
        $input = json_decode(file_get_contents('php://input'), true);

        if (!isset($input['week_start']) || !isset($input['entries'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Week start and entries required']);
            return;
        }

        try {
            // Calculate week end (Sunday)
            $weekStart = new DateTime($input['week_start']);
            $weekEnd = clone $weekStart;
            $weekEnd->add(new DateInterval('P6D'));

            $timesheetId = $this->generateUUID();

            $stmt = $this->db->prepare("
                INSERT INTO timesheets (id, user_id, user_name, week_start, week_end, entries, status) 
                VALUES (?, ?, ?, ?, ?, ?, 'draft')
            ");

            $stmt->execute([
                $timesheetId,
                $currentUser['id'],
                $currentUser['name'],
                $weekStart->format('Y-m-d'),
                $weekEnd->format('Y-m-d'),
                json_encode($input['entries'])
            ]);

            echo json_encode([
                'success' => true,
                'data' => [
                    'id' => $timesheetId,
                    'week_start' => $weekStart->format('Y-m-d'),
                    'week_end' => $weekEnd->format('Y-m-d'),
                    'user_name' => $currentUser['name'],
                    'entries' => $input['entries'],
                    'status' => 'draft'
                ],
                'message' => 'Timesheet created successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Timesheet creation failed']);
        }
    }

    public function updateTimesheet($currentUser, $timesheetId) {
        $input = json_decode(file_get_contents('php://input'), true);

        try {
            // Find timesheet
            $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);
            $timesheet = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$timesheet) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Timesheet not found']);
                return;
            }

            // Check permissions
            if (!$currentUser['is_admin'] && $timesheet['user_id'] !== $currentUser['id']) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'Access denied']);
                return;
            }

            // Update timesheet
            $updateFields = [];
            $updateValues = [];

            if (isset($input['week_start'])) {
                $weekStart = new DateTime($input['week_start']);
                $weekEnd = clone $weekStart;
                $weekEnd->add(new DateInterval('P6D'));
                
                $updateFields[] = "week_start = ?";
                $updateFields[] = "week_end = ?";
                $updateValues[] = $weekStart->format('Y-m-d');
                $updateValues[] = $weekEnd->format('Y-m-d');
            }

            if (isset($input['entries'])) {
                $updateFields[] = "entries = ?";
                $updateValues[] = json_encode($input['entries']);
            }

            if (!empty($updateFields)) {
                $updateValues[] = $timesheetId;
                $sql = "UPDATE timesheets SET " . implode(', ', $updateFields) . " WHERE id = ?";
                $stmt = $this->db->prepare($sql);
                $stmt->execute($updateValues);
            }

            echo json_encode([
                'success' => true,
                'message' => 'Timesheet updated successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Timesheet update failed']);
        }
    }

    public function deleteTimesheet($currentUser, $timesheetId) {
        try {
            // Find timesheet
            $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);
            $timesheet = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$timesheet) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Timesheet not found']);
                return;
            }

            // Check permissions
            if (!$currentUser['is_admin'] && $timesheet['user_id'] !== $currentUser['id']) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'Access denied']);
                return;
            }

            // Check if timesheet status allows deletion
            if ($timesheet['status'] !== 'draft') {
                http_response_code(400);
                echo json_encode([
                    'success' => false, 
                    'message' => 'Cannot delete timesheet that has been sent. Only draft timesheets can be deleted.'
                ]);
                return;
            }

            // Delete timesheet
            $stmt = $this->db->prepare("DELETE FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);

            echo json_encode([
                'success' => true,
                'message' => 'Timesheet deleted successfully'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Timesheet deletion failed']);
        }
    }

    public function generatePDF($currentUser, $timesheetId) {
        try {
            $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);
            $timesheet = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$timesheet) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Timesheet not found']);
                return;
            }

            // Check permissions
            if (!$currentUser['is_admin'] && $timesheet['user_id'] !== $currentUser['id']) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'Access denied']);
                return;
            }

            $timesheet['entries'] = json_decode($timesheet['entries'], true);
            
            $pdfGenerator = new PDFGenerator();
            $htmlContent = $pdfGenerator->generateTimesheetPDF($timesheet);
            $filename = $pdfGenerator->generateFilename($timesheet);

            header('Content-Type: text/html; charset=UTF-8');
            header('Content-Disposition: inline; filename="' . $filename . '"');
            
            echo $htmlContent;
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'PDF generation failed']);
        }
    }

    public function downloadAndEmail($currentUser, $timesheetId) {
        try {
            $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);
            $timesheet = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$timesheet) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Timesheet not found']);
                return;
            }

            // Check permissions
            if (!$currentUser['is_admin'] && $timesheet['user_id'] !== $currentUser['id']) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'Access denied']);
                return;
            }

            $timesheet['entries'] = json_decode($timesheet['entries'], true);

            $pdfGenerator = new PDFGenerator();
            $htmlContent = $pdfGenerator->generateTimesheetPDF($timesheet);
            $filename = $pdfGenerator->generateFilename($timesheet);

            // Try to send email
            try {
                $emailService = new EmailService($this->db);
                $emailService->sendTimesheetPDF($currentUser, $timesheet, $htmlContent, $filename);
                
                // Update status to sent
                $stmt = $this->db->prepare("UPDATE timesheets SET status = 'sent' WHERE id = ?");
                $stmt->execute([$timesheetId]);
            } catch (Exception $e) {
                // Continue with download even if email fails
                error_log("Email sending failed: " . $e->getMessage());
            }

            header('Content-Type: text/html; charset=UTF-8');
            header('Content-Disposition: inline; filename="' . $filename . '"');
            
            echo $htmlContent;
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Download and email failed']);
        }
    }

    public function sendEmail($currentUser, $timesheetId) {
        try {
            $stmt = $this->db->prepare("SELECT * FROM timesheets WHERE id = ?");
            $stmt->execute([$timesheetId]);
            $timesheet = $stmt->fetch(PDO::FETCH_ASSOC);

            if (!$timesheet) {
                http_response_code(404);
                echo json_encode(['success' => false, 'message' => 'Timesheet not found']);
                return;
            }

            // Check permissions
            if (!$currentUser['is_admin'] && $timesheet['user_id'] !== $currentUser['id']) {
                http_response_code(403);
                echo json_encode(['success' => false, 'message' => 'Access denied']);
                return;
            }

            $timesheet['entries'] = json_decode($timesheet['entries'], true);

            $pdfGenerator = new PDFGenerator();
            $htmlContent = $pdfGenerator->generateTimesheetPDF($timesheet);
            $filename = $pdfGenerator->generateFilename($timesheet);

            $emailService = new EmailService($this->db);
            $emailService->sendTimesheetPDF($currentUser, $timesheet, $htmlContent, $filename);

            // Update status to sent
            $stmt = $this->db->prepare("UPDATE timesheets SET status = 'sent' WHERE id = ?");
            $stmt->execute([$timesheetId]);

            echo json_encode([
                'success' => true,
                'message' => 'Email sent successfully'
            ]);
        } catch (Exception $e) {
            // Mark as sent even if email fails (user initiated the action)
            $stmt = $this->db->prepare("UPDATE timesheets SET status = 'sent' WHERE id = ?");
            $stmt->execute([$timesheetId]);
            
            http_response_code(500);
            echo json_encode(['success' => false, 'message' => 'Failed to send email: ' . $e->getMessage()]);
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