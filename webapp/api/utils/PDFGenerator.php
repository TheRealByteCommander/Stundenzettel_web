<?php
// Simple PDF generation using FPDF (included)
require_once __DIR__ . '/fpdf.php';

class PDFGenerator {
    private $companyInfo = [
        'name' => 'Schmitz Intralogistik GmbH',
        'address' => 'Grüner Weg 3',
        'city' => '04827 Machern',
        'country' => 'Deutschland'
    ];

    public function generateTimesheetPDF($timesheet) {
        $pdf = new FPDF('L', 'mm', 'A4'); // Landscape A4
        $pdf->AddPage();
        $pdf->SetFont('Arial', '', 12);
        
        // Company header (right aligned)
        $pdf->SetXY(200, 10);
        $pdf->SetFont('Arial', 'B', 8);
        $pdf->Cell(0, 4, $this->companyInfo['name'], 0, 1, 'R');
        $pdf->SetXY(200, 14);
        $pdf->SetFont('Arial', '', 8);
        $pdf->Cell(0, 4, $this->companyInfo['address'], 0, 1, 'R');
        $pdf->SetXY(200, 18);
        $pdf->Cell(0, 4, $this->companyInfo['city'] . ', ' . $this->companyInfo['country'], 0, 1, 'R');
        
        // Title
        $pdf->SetXY(10, 30);
        $pdf->SetFont('Arial', 'B', 18);
        $pdf->Cell(0, 10, 'STUNDENZETTEL', 0, 1, 'C');
        
        // Project/Customer info
        $entries = $timesheet['entries'];
        $projectInfo = '';
        $customerInfo = '';
        if (!empty($entries)) {
            $firstEntry = $entries[0];
            $projectInfo = !empty($firstEntry['customer_project']) ? $firstEntry['customer_project'] : '';
            $customerInfo = $projectInfo;
        }
        
        $pdf->SetXY(10, 50);
        $pdf->SetFont('Arial', '', 10);
        $pdf->Cell(130, 6, 'Projekt: ' . $projectInfo, 0, 0, 'L');
        $pdf->Cell(130, 6, 'Kunde: ' . $customerInfo, 0, 1, 'L');
        
        // Table header
        $pdf->SetXY(10, 65);
        $pdf->SetFont('Arial', 'B', 10);
        $pdf->SetFillColor(179, 179, 181); // Light gray
        
        $colWidths = [35, 25, 25, 20, 80, 25];
        $headers = ['Datum', 'Startzeit', 'Endzeit', 'Pause', 'Beschreibung', 'Arbeitszeit'];
        
        for ($i = 0; $i < count($headers); $i++) {
            $pdf->Cell($colWidths[$i], 8, $headers[$i], 1, 0, 'C', true);
        }
        $pdf->Ln();
        
        // Table data
        $pdf->SetFont('Arial', '', 9);
        $pdf->SetFillColor(255, 255, 255); // White
        
        $dayNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
        $totalHours = 0;
        $weekStart = new DateTime($timesheet['week_start']);
        
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
                    $description = !empty($entry['tasks']) ? substr($entry['tasks'], 0, 40) : '';
                    break;
                }
            }
            
            $pdf->Cell($colWidths[0], 8, $dayName, 1, 0, 'C');
            $pdf->Cell($colWidths[1], 8, $startTime, 1, 0, 'C');
            $pdf->Cell($colWidths[2], 8, $endTime, 1, 0, 'C');
            $pdf->Cell($colWidths[3], 8, $breakMinutes, 1, 0, 'C');
            $pdf->Cell($colWidths[4], 8, $description, 1, 0, 'L');
            $pdf->Cell($colWidths[5], 8, $workHours, 1, 1, 'C');
        }
        
        // Total row
        $pdf->SetFont('Arial', 'B', 10);
        $pdf->SetFillColor(179, 179, 181); // Light gray
        $pdf->Cell($colWidths[0] + $colWidths[1] + $colWidths[2] + $colWidths[3], 8, '', 1, 0, 'C', true);
        $pdf->Cell($colWidths[4], 8, 'Gesamtstunden:', 1, 0, 'C', true);
        $pdf->Cell($colWidths[5], 8, number_format($totalHours, 1) . 'h', 1, 1, 'C', true);
        
        // Signatures
        $pdf->SetXY(10, 170);
        $pdf->SetFont('Arial', '', 10);
        $createdAt = new DateTime($timesheet['created_at']);
        $pdf->Cell(130, 6, 'Datum: ' . $createdAt->format('d.m.Y'), 0, 1, 'L');
        $pdf->Cell(130, 6, 'Mitarbeiter: ' . $timesheet['user_name'], 0, 1, 'L');
        $pdf->Ln(5);
        $pdf->Cell(130, 6, 'Unterschrift Mitarbeiter: ______________________________', 0, 0, 'L');
        $pdf->Cell(130, 6, 'Unterschrift Kunde: ______________________________', 0, 1, 'L');
        
        return $pdf->Output('S'); // Return as string
    }

    public function generateFilename($timesheet) {
        $weekStart = new DateTime($timesheet['week_start']);
        $weekNumber = (int)$weekStart->format('W');
        $cleanName = preg_replace('/[^\w\-_.]/', '_', $timesheet['user_name']);
        $cleanName = preg_replace('/_+/', '_', $cleanName);
        
        $sequentialNumber = '001';
        
        return "{$cleanName}_KW" . str_pad($weekNumber, 2, '0', STR_PAD_LEFT) . "_{$sequentialNumber}.pdf";
    }
}
?>