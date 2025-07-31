<?php
// Simple HTML-based PDF generation
class PDFGenerator {
    private $companyInfo = [
        'name' => 'Schmitz Intralogistik GmbH',
        'address' => 'Grüner Weg 3',
        'city' => '04827 Machern',
        'country' => 'Deutschland'
    ];

    public function generateTimesheetPDF($timesheet) {
        // For now, return HTML that can be printed as PDF by browser
        return $this->generateHTML($timesheet);
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
                        $startTime = htmlspecialchars($entry['start_time']);
                        $endTime = htmlspecialchars($entry['end_time']);
                        $breakMinutes = htmlspecialchars($entry['break_minutes']) . ' Min';
                        
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
                    $description = !empty($entry['tasks']) ? htmlspecialchars(substr($entry['tasks'], 0, 60)) : '';
                    break;
                }
            }
            
            $tableRows .= "
                <tr>
                    <td class='day-name'>{$dayName}</td>
                    <td class='time-cell'>{$startTime}</td>
                    <td class='time-cell'>{$endTime}</td>
                    <td class='time-cell'>{$breakMinutes}</td>
                    <td class='description-cell'>{$description}</td>
                    <td class='time-cell'>{$workHours}</td>
                </tr>
            ";
        }
        
        // Get project and customer info from first entry
        $projectInfo = '';
        $customerInfo = '';
        if (!empty($entries)) {
            $firstEntry = $entries[0];
            $projectInfo = !empty($firstEntry['customer_project']) ? htmlspecialchars($firstEntry['customer_project']) : '';
            $customerInfo = $projectInfo; // Same for now
        }
        
        $createdAt = new DateTime($timesheet['created_at']);
        $totalHoursFormatted = number_format($totalHours, 1);
        $userName = htmlspecialchars($timesheet['user_name']);

        return "
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='UTF-8'>
            <title>Stundenzettel - {$userName}</title>
            <style>
                @page {
                    size: A4 landscape;
                    margin: 15mm;
                }
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    font-size: 10px;
                    color: #5a5a5a;
                    line-height: 1.2;
                }
                .header {
                    text-align: center;
                    margin-bottom: 15px;
                }
                .company-info {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    font-size: 8px;
                    text-align: right;
                }
                .project-info {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    font-size: 10px;
                }
                .project-info div {
                    flex: 1;
                }
                .timesheet-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 15px;
                    font-size: 9px;
                }
                .timesheet-table th {
                    background-color: #b3b3b5;
                    padding: 6px 4px;
                    border: 1px solid #000;
                    text-align: center;
                    font-weight: bold;
                    font-size: 9px;
                }
                .timesheet-table td {
                    padding: 4px;
                    border: 1px solid #000;
                    text-align: center;
                }
                .day-name {
                    font-weight: bold;
                    text-align: center !important;
                }
                .time-cell {
                    text-align: center !important;
                }
                .description-cell {
                    text-align: left !important;
                    font-size: 8px;
                }
                .total-row {
                    background-color: #b3b3b5;
                    font-weight: bold;
                }
                .signatures {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 20px;
                    font-size: 9px;
                }
                .signature-field {
                    flex: 1;
                    margin: 0 10px;
                }
                h1 {
                    font-size: 16px;
                    margin: 0;
                    color: #5a5a5a;
                }
                @media print {
                    body { -webkit-print-color-adjust: exact; }
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
                <h1>STUNDENZETTEL</h1>
            </div>

            <div class='project-info'>
                <div><strong>Projekt:</strong> {$projectInfo}</div>
                <div><strong>Kunde:</strong> {$customerInfo}</div>
            </div>

            <table class='timesheet-table'>
                <thead>
                    <tr>
                        <th style='width: 15%;'>Datum</th>
                        <th style='width: 12%;'>Startzeit</th>
                        <th style='width: 12%;'>Endzeit</th>
                        <th style='width: 10%;'>Pause</th>
                        <th style='width: 36%;'>Beschreibung</th>
                        <th style='width: 15%;'>Arbeitszeit</th>
                    </tr>
                </thead>
                <tbody>
                    {$tableRows}
                    <tr class='total-row'>
                        <td colspan='4'></td>
                        <td style='font-weight: bold;'>Gesamtstunden:</td>
                        <td style='font-weight: bold;'>{$totalHoursFormatted}h</td>
                    </tr>
                </tbody>
            </table>

            <div class='signatures'>
                <div class='signature-field'>
                    <strong>Datum:</strong> {$createdAt->format('d.m.Y')}<br><br>
                    <strong>Mitarbeiter:</strong> {$userName}<br><br>
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
        
        $sequentialNumber = '001';
        
        return "{$cleanName}_KW" . str_pad($weekNumber, 2, '0', STR_PAD_LEFT) . "_{$sequentialNumber}.html";
    }
}
?>