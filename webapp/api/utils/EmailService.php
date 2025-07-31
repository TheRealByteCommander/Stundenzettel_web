<?php
// Simple email service using PHP mail() function
class EmailService {
    private $db;

    public function __construct($db) {
        $this->db = $db;
    }

    public function sendTimesheetPDF($currentUser, $timesheet, $htmlContent, $filename) {
        // Get SMTP configuration
        $stmt = $this->db->prepare("SELECT * FROM smtp_config ORDER BY created_at DESC LIMIT 1");
        $stmt->execute();
        $smtpConfig = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$smtpConfig) {
            throw new Exception('SMTP configuration not found. Please contact admin.');
        }

        $weekStart = new DateTime($timesheet['week_start']);
        $weekEnd = new DateTime($timesheet['week_end']);
        
        $subject = "Stundenzettel - {$timesheet['user_name']} - Woche {$timesheet['week_start']}";
        
        $body = "
        <html>
        <body style='font-family: Arial, sans-serif;'>
            <h2>Stundenzettel</h2>
            <p>Hallo {$timesheet['user_name']},</p>
            <p>anbei finden Sie Ihren Stundenzettel für die Woche vom {$weekStart->format('d.m.Y')} bis {$weekEnd->format('d.m.Y')}.</p>
            <p>Sie können den Stundenzettel direkt in Ihrem Browser drucken oder als PDF speichern.</p>
            <br>
            <p>Mit freundlichen Grüßen<br>
            <strong>Schmitz Intralogistik GmbH</strong><br>
            Grüner Weg 3<br>
            04827 Machern, Deutschland</p>
        </body>
        </html>";

        // Headers for HTML email
        $headers = "MIME-Version: 1.0" . "\r\n";
        $headers .= "Content-type:text/html;charset=UTF-8" . "\r\n";
        $headers .= "From: {$smtpConfig['smtp_username']}" . "\r\n";
        $headers .= "Cc: {$smtpConfig['admin_email']}" . "\r\n";

        // Send email
        if (!mail($currentUser['email'], $subject, $body, $headers)) {
            throw new Exception("Email sending failed. Please check server configuration.");
        }
    }

    public function sendDownloadNotification($currentUser, $timesheet, $filename) {
        // Get SMTP configuration
        $stmt = $this->db->prepare("SELECT * FROM smtp_config ORDER BY created_at DESC LIMIT 1");
        $stmt->execute();
        $smtpConfig = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$smtpConfig) {
            return; // Skip if no SMTP config
        }

        $weekStart = new DateTime($timesheet['week_start']);
        $weekEnd = new DateTime($timesheet['week_end']);
        
        $subject = "Stundenzettel Download - {$timesheet['user_name']} - KW" . $weekStart->format('W');
        
        $body = "
        <html>
        <body style='font-family: Arial, sans-serif;'>
            <h2>Stundenzettel Download</h2>
            <p>Hallo {$currentUser['name']},</p>
            <p>Sie haben den Stundenzettel für die Woche vom {$weekStart->format('d.m.Y')} bis {$weekEnd->format('d.m.Y')} heruntergeladen.</p>
            <p>Eine Kopie wurde automatisch an die Admin-Adresse gesendet.</p>
            <p><strong>Dateiname:</strong> {$filename}</p>
            <br>
            <p>Mit freundlichen Grüßen<br>
            <strong>Schmitz Intralogistik GmbH</strong></p>
        </body>
        </html>";

        $headers = "MIME-Version: 1.0" . "\r\n";
        $headers .= "Content-type:text/html;charset=UTF-8" . "\r\n";
        $headers .= "From: {$smtpConfig['smtp_username']}" . "\r\n";
        $headers .= "Cc: {$smtpConfig['admin_email']}" . "\r\n";

        // Don't throw exception for notification emails
        mail($currentUser['email'], $subject, $body, $headers);
    }
}
?>