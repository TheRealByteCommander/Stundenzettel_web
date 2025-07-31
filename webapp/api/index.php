<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once 'config/database.php';
require_once 'controllers/AuthController.php';
require_once 'controllers/TimesheetController.php';
require_once 'controllers/UserController.php';
require_once 'controllers/AdminController.php';
require_once 'middleware/AuthMiddleware.php';

// Simple router
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$uri = str_replace('/api', '', $uri);
$uri = trim($uri, '/');
$method = $_SERVER['REQUEST_METHOD'];

// Initialize database
$database = new Database();
$db = $database->getConnection();

// Initialize controllers
$authController = new AuthController($db);
$timesheetController = new TimesheetController($db);
$userController = new UserController($db);
$adminController = new AdminController($db);
$authMiddleware = new AuthMiddleware($db);

// Route handling
try {
    switch (true) {
        // Authentication routes
        case $uri === 'auth/login' && $method === 'POST':
            $authController->login();
            break;
            
        case $uri === 'auth/register' && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $authController->register($user);
            break;
            
        case $uri === 'auth/me' && $method === 'GET':
            $user = $authMiddleware->requireAuth();
            $authController->me($user);
            break;
            
        case $uri === 'auth/change-password' && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $authController->changePassword($user);
            break;

        // Timesheet routes
        case $uri === 'timesheets' && $method === 'GET':
            $user = $authMiddleware->requireAuth();
            $timesheetController->getTimesheets($user);
            break;
            
        case $uri === 'timesheets' && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $timesheetController->createTimesheet($user);
            break;
            
        case preg_match('/^timesheets\/([a-f0-9-]+)$/', $uri, $matches) && $method === 'PUT':
            $user = $authMiddleware->requireAuth();
            $timesheetController->updateTimesheet($user, $matches[1]);
            break;
            
        case preg_match('/^timesheets\/([a-f0-9-]+)$/', $uri, $matches) && $method === 'DELETE':
            $user = $authMiddleware->requireAuth();
            $timesheetController->deleteTimesheet($user, $matches[1]);
            break;
            
        case preg_match('/^timesheets\/([a-f0-9-]+)\/pdf$/', $uri, $matches) && $method === 'GET':
            $user = $authMiddleware->requireAuth();
            $timesheetController->generatePDF($user, $matches[1]);
            break;
            
        case preg_match('/^timesheets\/([a-f0-9-]+)\/download-and-email$/', $uri, $matches) && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $timesheetController->downloadAndEmail($user, $matches[1]);
            break;
            
        case preg_match('/^timesheets\/([a-f0-9-]+)\/send-email$/', $uri, $matches) && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $timesheetController->sendEmail($user, $matches[1]);
            break;

        // User management routes
        case $uri === 'users' && $method === 'GET':
            $user = $authMiddleware->requireAuth();
            $userController->getUsers($user);
            break;
            
        case preg_match('/^users\/([a-f0-9-]+)$/', $uri, $matches) && $method === 'PUT':
            $user = $authMiddleware->requireAuth();
            $userController->updateUser($user, $matches[1]);
            break;
            
        case preg_match('/^users\/([a-f0-9-]+)$/', $uri, $matches) && $method === 'DELETE':
            $user = $authMiddleware->requireAuth();
            $userController->deleteUser($user, $matches[1]);
            break;

        // Admin routes
        case $uri === 'admin/smtp-config' && $method === 'POST':
            $user = $authMiddleware->requireAuth();
            $adminController->saveSmtpConfig($user);
            break;
            
        case $uri === 'admin/smtp-config' && $method === 'GET':
            $user = $authMiddleware->requireAuth();
            $adminController->getSmtpConfig($user);
            break;

        default:
            http_response_code(404);
            echo json_encode(['success' => false, 'message' => 'Endpoint not found']);
            break;
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => $e->getMessage()]);
}
?>