<?php
// Professional PDF generation using TCPDF
require_once __DIR__ . '/tcpdf/tcpdf.php';

class PDFGenerator {
    private $companyInfo = [
        'name' => 'Schmitz Intralogistik GmbH',
        'address' => 'Grüner Weg 3',
        'city' => '04827 Machern',
        'country' => 'Deutschland'
    ];

    public function generateTimesheetPDF($timesheet) {
        // Create new PDF document in landscape format
        $pdf = new TCPDF('L', PDF_UNIT, 'A4', true, 'UTF-8', false);
        
        // Set document information
        $pdf->SetCreator('Schmitz Intralogistik GmbH');
        $pdf->SetAuthor('Schmitz Intralogistik GmbH');
        $pdf->SetTitle('Stundenzettel - ' . $timesheet['user_name']);
        $pdf->SetSubject('Wöchentlicher Stundenzettel');
        
        // Remove default header/footer
        $pdf->setPrintHeader(false);
        $pdf->setPrintFooter(false);
        
        // Set margins
        $pdf->SetMargins(15, 15, 15);
        $pdf->SetAutoPageBreak(TRUE, 15);
        
        // Add a page
        $pdf->AddPage();
        
        // Company colors
        $companyRed = array(233, 1, 24);      // #e90118
        $lightGray = array(179, 179, 181);    // #b3b3b5
        $darkGray = array(90, 90, 90);        // #5a5a5a
        
        // Company header (right aligned)
        $pdf->SetFont('helvetica', 'B', 9);
        $pdf->SetTextColor($darkGray[0], $darkGray[1], $darkGray[2]);
        $pdf->SetXY(200, 15);
        $pdf->Cell(80, 5, $this->companyInfo['name'], 0, 1, 'R');
        
        $pdf->SetFont('helvetica', '', 8);
        $pdf->SetXY(200, 20);
        $pdf->Cell(80, 4, $this->companyInfo['address'], 0, 1, 'R');
        $pdf->SetXY(200, 24);
        $pdf->Cell(80, 4, $this->companyInfo['city'] . ', ' . $this->companyInfo['country'], 0, 1, 'R');
        
        // Main title
        $pdf->SetFont('helvetica', 'B', 20);
        $pdf->SetTextColor($darkGray[0], $darkGray[1], $darkGray[2]);
        $pdf->SetXY(15, 35);
        $pdf->Cell(0, 12, 'STUNDENZETTEL', 0, 1, 'C');
        
        // Get project and customer info from first entry
        $entries = $timesheet['entries'];
        $projectInfo = '';
        $customerInfo = '';
        if (!empty($entries)) {
            $firstEntry = $entries[0];
            $projectInfo = !empty($firstEntry['customer_project']) ? $firstEntry['customer_project'] : '';
            $customerInfo = $projectInfo; // Same for now
        }
        
        // Project/Customer info
        $pdf->SetFont('helvetica', '', 11);
        $pdf->SetXY(15, 55);
        $pdf->Cell(120, 6, 'Projekt: ' . $projectInfo, 0, 0, 'L');
        $pdf->Cell(120, 6, 'Kunde: ' . $customerInfo, 0, 1, 'L');
        
        // Employee and week info
        $weekStart = new DateTime($timesheet['week_start']);
        $weekEnd = new DateTime($timesheet['week_end']);
        $weekNumber = $weekStart->format('W');
        
        $pdf->SetXY(15, 65);
        $pdf->Cell(120, 6, 'Mitarbeiter: ' . $timesheet['user_name'], 0, 0, 'L');
        $pdf->Cell(120, 6, 'Kalenderwoche: ' . $weekNumber . ' (' . $weekStart->format('d.m.Y') . ' - ' . $weekEnd->format('d.m.Y') . ')', 0, 1, 'L');
        
        // Table starts at Y=80
        $tableY = 80;
        
        // Table headers
        $pdf->SetFont('helvetica', 'B', 10);
        $pdf->SetFillColor($lightGray[0], $lightGray[1], $lightGray[2]);
        $pdf->SetTextColor(0, 0, 0);
        
        $headers = ['Datum', 'Startzeit', 'Endzeit', 'Pause', 'Beschreibung', 'Arbeitszeit'];
        $colWidths = [40, 25, 25, 20, 90, 30];
        
        $pdf->SetXY(15, $tableY);
        for ($i = 0; $i < count($headers); $i++) {
            $pdf->Cell($colWidths[$i], 10, $headers[$i], 1, 0, 'C', true);
        }
        $pdf->Ln();
        
        // Table data
        $pdf->SetFont('helvetica', '', 9);
        $pdf->SetFillColor(255, 255, 255);
        $pdf->SetTextColor($darkGray[0], $darkGray[1], $darkGray[2]);
        
        $dayNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
        $totalHours = 0;
        
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
            
            $rowY = $tableY + 10 + ($i * 10);
            $pdf->SetXY(15, $rowY);
            
            // Use bold font for day names
            $pdf->SetFont('helvetica', 'B', 9);
            $pdf->Cell($colWidths[0], 10, $dayName, 1, 0, 'C', true);
            
            $pdf->SetFont('helvetica', '', 9);
            $pdf->Cell($colWidths[1], 10, $startTime, 1, 0, 'C', true);
            $pdf->Cell($colWidths[2], 10, $endTime, 1, 0, 'C', true);
            $pdf->Cell($colWidths[3], 10, $breakMinutes, 1, 0, 'C', true);
            $pdf->Cell($colWidths[4], 10, $description, 1, 0, 'L', true);
            $pdf->Cell($colWidths[5], 10, $workHours, 1, 0, 'C', true);
        }
        
        // Total row
        $totalRowY = $tableY + 10 + (7 * 10);
        $pdf->SetXY(15, $totalRowY);
        $pdf->SetFont('helvetica', 'B', 10);
        $pdf->SetFillColor($lightGray[0], $lightGray[1], $lightGray[2]);
        
        $pdf->Cell($colWidths[0] + $colWidths[1] + $colWidths[2] + $colWidths[3], 10, '', 1, 0, 'C', true);
        $pdf->Cell($colWidths[4], 10, 'Gesamtstunden:', 1, 0, 'C', true);
        $pdf->Cell($colWidths[5], 10, number_format($totalHours, 1) . 'h', 1, 0, 'C', true);
        
        // Signatures
        $signatureY = $totalRowY + 25;
        $pdf->SetFont('helvetica', '', 10);
        $pdf->SetTextColor($darkGray[0], $darkGray[1], $darkGray[2]);
        
        $createdAt = new DateTime($timesheet['created_at']);
        
        $pdf->SetXY(15, $signatureY);
        $pdf->Cell(120, 6, 'Datum: ' . $createdAt->format('d.m.Y'), 0, 0, 'L');
        $pdf->Cell(120, 6, 'Unterschrift Kunde: ________________________________', 0, 1, 'L');
        
        $pdf->SetXY(15, $signatureY + 10);
        $pdf->Cell(120, 6, 'Mitarbeiter: ' . $timesheet['user_name'], 0, 0, 'L');
        $pdf->Cell(120, 6, 'Unterschrift Mitarbeiter: __________________________', 0, 1, 'L');
        
        return $pdf->Output('', 'S'); // Return as string
    }

    public function generateFilename($timesheet) {
        $weekStart = new DateTime($timesheet['week_start']);
        $weekNumber = (int)$weekStart->format('W');
        $year = $weekStart->format('Y');
        
        // Clean employee name for filename
        $cleanName = preg_replace('/[^\w\-_.]/', '_', $timesheet['user_name']);
        $cleanName = preg_replace('/_+/', '_', $cleanName);
        $cleanName = trim($cleanName, '_');
        
        // Generate sequential number based on existing timesheets for this week
        $sequentialNumber = '001'; // Default, could be enhanced to check DB for existing files
        
        return "{$cleanName}_KW" . str_pad($weekNumber, 2, '0', STR_PAD_LEFT) . "_{$year}_{$sequentialNumber}.pdf";
    }
}
?>