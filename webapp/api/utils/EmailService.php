<?php
require_once __DIR__ . '/../vendor/autoload.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

class EmailService {
    private $db;

    public function __construct($db) {
        $this->db = $db;
    }

    public function sendTimesheetPDF($currentUser, $timesheet, $pdfContent, $filename) {
        // Get SMTP configuration
        $stmt = $this->db->prepare("SELECT * FROM smtp_config ORDER BY created_at DESC LIMIT 1");
        $stmt->execute();
        $smtpConfig = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$smtpConfig) {
            throw new Exception('SMTP configuration not found. Please contact admin.');
        }

        $mail = new PHPMailer(true);

        try {
            // Server settings
            $mail->isSMTP();
            $mail->Host = $smtpConfig['smtp_server'];
            $mail->SMTPAuth = true;
            $mail->Username = $smtpConfig['smtp_username'];
            $mail->Password = $smtpConfig['smtp_password'];
            $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
            $mail->Port = $smtpConfig['smtp_port'];
            $mail->CharSet = 'UTF-8';

            // Recipients
            $mail->setFrom($smtpConfig['smtp_username'], 'Schmitz Intralogistik GmbH');
            $mail->addAddress($currentUser['email'], $currentUser['name']);
            $mail->addCC($smtpConfig['admin_email']);

            // Attachments
            $mail->addStringAttachment($pdfContent, $filename, 'base64', 'application/pdf');

            // Content
            $mail->isHTML(true);
            $mail->Subject = "Stundenzettel - {$timesheet['user_name']} - Woche {$timesheet['week_start']}";
            
            $weekStart = new DateTime($timesheet['week_start']);
            $weekEnd = new DateTime($timesheet['week_end']);
            
            $mail->Body = "
                <html>
                <body style='font-family: Arial, sans-serif;'>
                    <h2>Stundenzettel</h2>
                    <p>Hallo {$timesheet['user_name']},</p>
                    <p>anbei finden Sie Ihren Stundenzettel für die Woche vom {$weekStart->format('d.m.Y')} bis {$weekEnd->format('d.m.Y')}.</p>
                    <br>
                    <p>Mit freundlichen Grüßen<br>
                    <strong>Schmitz Intralogistik GmbH</strong><br>
                    Grüner Weg 3<br>
                    04827 Machern, Deutschland</p>
                </body>
                </html>
            ";

            $mail->AltBody = "Hallo {$timesheet['user_name']},\n\nanbei finden Sie Ihren Stundenzettel für die Woche vom {$weekStart->format('d.m.Y')} bis {$weekEnd->format('d.m.Y')}.\n\nMit freundlichen Grüßen\nSchmitz Intralogistik GmbH";

            $mail->send();
        } catch (Exception $e) {
            throw new Exception("Email sending failed: {$mail->ErrorInfo}");
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

        $mail = new PHPMailer(true);

        try {
            // Server settings
            $mail->isSMTP();
            $mail->Host = $smtpConfig['smtp_server'];
            $mail->SMTPAuth = true;
            $mail->Username = $smtpConfig['smtp_username'];
            $mail->Password = $smtpConfig['smtp_password'];
            $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
            $mail->Port = $smtpConfig['smtp_port'];
            $mail->CharSet = 'UTF-8';

            // Recipients
            $mail->setFrom($smtpConfig['smtp_username'], 'Schmitz Intralogistik GmbH');
            $mail->addAddress($currentUser['email'], $currentUser['name']);
            $mail->addCC($smtpConfig['admin_email']);

            // Content
            $mail->isHTML(true);
            $mail->Subject = "Stundenzettel Download - {$timesheet['user_name']} - KW" . (new DateTime($timesheet['week_start']))->format('W');
            
            $weekStart = new DateTime($timesheet['week_start']);
            $weekEnd = new DateTime($timesheet['week_end']);
            
            $mail->Body = "
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
                </html>
            ";

            $mail->send();
        } catch (Exception $e) {
            // Don't throw exception for notification emails
            error_log("Download notification email failed: " . $e->getMessage());
        }
    }
}
?>