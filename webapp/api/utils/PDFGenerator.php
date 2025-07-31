<?php
require_once __DIR__ . '/../vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

class PDFGenerator {
    private $companyInfo = [
        'name' => 'Schmitz Intralogistik GmbH',
        'address' => 'Grüner Weg 3',
        'city' => '04827 Machern',
        'country' => 'Deutschland'
    ];

    public function generateTimesheetPDF($timesheet) {
        $options = new Options();
        $options->set('defaultFont', 'Arial');
        $options->set('isRemoteEnabled', true);

        $dompdf = new Dompdf($options);
        
        $html = $this->generateHTML($timesheet);
        $dompdf->loadHtml($html);
        
        // Set paper size to A4 landscape
        $dompdf->setPaper('A4', 'landscape');
        
        $dompdf->render();
        
        return $dompdf->output();
    }

    private function generateHTML($timesheet) {
        $entries = $timesheet['entries'];
        $dayNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
        
        // Calculate total hours
        $totalHours = 0;
        $weekStart = new DateTime($timesheet['week_start']);
        
        // Build table rows
        $tableRows = '';
        for ($i = 0; $i < 7; $i++) {
            $currentDate = clone $weekStart;
            $currentDate->add(new DateInterval("P{$i}D"));
            $dateStr = $currentDate->format('Y-m-d');
            
            $dayName = $dayNames[$i];
            $startTime = '';
            $endTime = '';
            $breakMinutes = '';
            $description = '';
            $workHours = '';
            
            // Find entry for this date
            foreach ($entries as $entry) {
                if ($entry['date'] === $dateStr) {
                    if (!empty($entry['start_time']) && !empty($entry['end_time'])) {
                        $startTime = $entry['start_time'];
                        $endTime = $entry['end_time'];
                        $breakMinutes = $entry['break_minutes'] . ' Min';
                        
                        // Calculate daily hours
                        $startParts = explode(':', $entry['start_time']);
                        $endParts = explode(':', $entry['end_time']);
                        $startMinutes = (int)$startParts[0] * 60 + (int)$startParts[1];
                        $endMinutes = (int)$endParts[0] * 60 + (int)$endParts[1];
                        $workedMinutes = $endMinutes - $startMinutes - $entry['break_minutes'];
                        $dailyHours = $workedMinutes / 60;
                        $totalHours += $dailyHours;
                        $workHours = number_format($dailyHours, 1) . 'h';
                    }
                    $description = !empty($entry['tasks']) ? $entry['tasks'] : '';
                    break;
                }
            }
            
            $tableRows .= "
                <tr>
                    <td style='padding: 8px; border: 1px solid #000; text-align: center; font-weight: bold;'>{$dayName}</td>
                    <td style='padding: 8px; border: 1px solid #000; text-align: center;'>{$startTime}</td>
                    <td style='padding: 8px; border: 1px solid #000; text-align: center;'>{$endTime}</td>
                    <td style='padding: 8px; border: 1px solid #000; text-align: center;'>{$breakMinutes}</td>
                    <td style='padding: 8px; border: 1px solid #000; font-size: 10px;'>{$description}</td>
                    <td style='padding: 8px; border: 1px solid #000; text-align: center;'>{$workHours}</td>
                </tr>
            ";
        }
        
        // Get project and customer info from first entry
        $projectInfo = '';
        $customerInfo = '';
        if (!empty($entries)) {
            $firstEntry = $entries[0];
            $projectInfo = !empty($firstEntry['customer_project']) ? $firstEntry['customer_project'] : '';
            $customerInfo = $projectInfo; // Same for now
        }
        
        $createdAt = new DateTime($timesheet['created_at']);
        $totalHoursFormatted = number_format($totalHours, 1);

        return "
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='UTF-8'>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    font-size: 11px;
                    color: #5a5a5a;
                }
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .company-info {
                    text-align: right;
                    font-size: 9px;
                    margin-bottom: 20px;
                }
                .project-info {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                    font-size: 11px;
                }
                .project-info div {
                    flex: 1;
                }
                .timesheet-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                .timesheet-table th {
                    background-color: #b3b3b5;
                    padding: 10px;
                    border: 1px solid #000;
                    text-align: center;
                    font-weight: bold;
                }
                .total-row {
                    background-color: #b3b3b5;
                    font-weight: bold;
                }
                .signatures {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 30px;
                }
                .signature-field {
                    flex: 1;
                    margin: 0 20px;
                }
            </style>
        </head>
        <body>
            <div class='company-info'>
                <strong>Schmitz Intralogistik GmbH</strong><br>
                Grüner Weg 3<br>
                04827 Machern, Deutschland
            </div>

            <div class='header'>
                <h1 style='font-size: 20px; margin: 0; color: #5a5a5a;'>STUNDENZETTEL</h1>
            </div>

            <div class='project-info'>
                <div><strong>Projekt:</strong> {$projectInfo}</div>
                <div><strong>Kunde:</strong> {$customerInfo}</div>
            </div>

            <table class='timesheet-table'>
                <thead>
                    <tr>
                        <th style='width: 15%;'>Datum</th>
                        <th style='width: 15%;'>Startzeit</th>
                        <th style='width: 15%;'>Endzeit</th>
                        <th style='width: 10%;'>Pause</th>
                        <th style='width: 30%;'>Beschreibung</th>
                        <th style='width: 15%;'>Arbeitszeit</th>
                    </tr>
                </thead>
                <tbody>
                    {$tableRows}
                    <tr class='total-row'>
                        <td colspan='4' style='padding: 10px; border: 1px solid #000; text-align: center;'></td>
                        <td style='padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;'>Gesamtstunden:</td>
                        <td style='padding: 10px; border: 1px solid #000; text-align: center; font-weight: bold;'>{$totalHoursFormatted}h</td>
                    </tr>
                </tbody>
            </table>

            <div class='signatures'>
                <div class='signature-field'>
                    <strong>Datum:</strong> {$createdAt->format('d.m.Y')}<br><br>
                    <strong>Mitarbeiter:</strong> {$timesheet['user_name']}<br><br>
                    <strong>Unterschrift Mitarbeiter:</strong> ______________________________
                </div>
                <div class='signature-field'>
                    <br><br><br><br>
                    <strong>Unterschrift Kunde:</strong> ______________________________
                </div>
            </div>
        </body>
        </html>
        ";
    }

    public function generateFilename($timesheet) {
        $weekStart = new DateTime($timesheet['week_start']);
        $weekNumber = (int)$weekStart->format('W');
        $cleanName = preg_replace('/[^\w\-_.]/', '_', $timesheet['user_name']);
        $cleanName = preg_replace('/_+/', '_', $cleanName);
        
        // For sequential number, we'll use 001 for now
        // In a full implementation, you'd query the database for existing timesheets
        $sequentialNumber = '001';
        
        return "{$cleanName}_KW" . str_pad($weekNumber, 2, '0', STR_PAD_LEFT) . "_{$sequentialNumber}.pdf";
    }
}
?>