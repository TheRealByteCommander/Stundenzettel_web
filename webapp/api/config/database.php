<?php
class Database {
    private $host = 'localhost';
    private $database = 'd04464c7';
    private $username = 'd04464c7';
    private $password = 'mAh4Raeder!';
    private $conn;

    public function getConnection() {
        $this->conn = null;

        try {
            $this->conn = new PDO(
                "mysql:host=" . $this->host . ";dbname=" . $this->database . ";charset=utf8",
                $this->username,
                $this->password
            );
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $exception) {
            error_log("Connection error: " . $exception->getMessage());
            throw new Exception("Database connection failed");
        }

        return $this->conn;
    }

    public function initializeDatabase() {
        try {
            // Connect to the specific database
            $this->conn = $this->getConnection();
            
            // Create tables
            $this->createTables();
            $this->createDefaultAdmin();
            
        } catch(PDOException $exception) {
            error_log("Database initialization error: " . $exception->getMessage());
            throw new Exception("Database initialization failed");
        }
    }

    private function createTables() {
        // Users table
        $usersTable = "
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ";

        // Timesheets table
        $timesheetsTable = "
            CREATE TABLE IF NOT EXISTS timesheets (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                entries JSON NOT NULL,
                status ENUM('draft', 'sent') DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_date (user_id, week_start),
                INDEX idx_status (status),
                INDEX idx_created (created_at)
            )
        ";

        // SMTP config table
        $smtpConfigTable = "
            CREATE TABLE IF NOT EXISTS smtp_config (
                id VARCHAR(36) PRIMARY KEY,
                smtp_server VARCHAR(255) NOT NULL,
                smtp_port INT NOT NULL DEFAULT 587,
                smtp_username VARCHAR(255) NOT NULL,
                smtp_password VARCHAR(255) NOT NULL,
                admin_email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ";

        $this->conn->exec($usersTable);
        $this->conn->exec($timesheetsTable);
        $this->conn->exec($smtpConfigTable);
    }

    private function createDefaultAdmin() {
        // Check if admin exists
        $stmt = $this->conn->prepare("SELECT COUNT(*) FROM users WHERE email = ?");
        $stmt->execute(['admin@schmitz-intralogistik.de']);
        
        if ($stmt->fetchColumn() == 0) {
            // Create default admin
            $stmt = $this->conn->prepare("
                INSERT INTO users (id, email, name, password_hash, is_admin) 
                VALUES (?, ?, ?, ?, ?)
            ");
            
            $stmt->execute([
                $this->generateUUID(),
                'admin@schmitz-intralogistik.de',
                'Administrator',
                password_hash('admin123', PASSWORD_DEFAULT),
                true
            ]);
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