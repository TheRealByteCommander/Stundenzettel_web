import type { WeeklyTimesheet } from "../services/api/types";

/**
 * Export data to CSV format
 */
export const exportToCSV = (data: any[], filename: string, headers?: string[]) => {
  const csvHeaders = headers || Object.keys(data[0] || {});
  const rows = data.map((row) =>
    csvHeaders.map((header) => {
      const value = row[header];
      // Escape quotes and wrap in quotes
      return `"${String(value || "").replace(/"/g, '""')}"`;
    })
  );

  const csvContent = [csvHeaders.join(","), ...rows.map((row) => row.join(","))].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export data to JSON format
 */
export const exportToJSON = (data: any[], filename: string) => {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export data to Excel format (XLSX) using a simple XML-based format
 * Note: This creates a basic Excel-compatible XML file
 */
export const exportToExcel = (data: any[], filename: string, sheetName = "Sheet1") => {
  // Create Excel XML format (SpreadsheetML)
  const headers = Object.keys(data[0] || {});
  
  let xml = '<?xml version="1.0"?>\n';
  xml += '<?mso-application progid="Excel.Sheet"?>\n';
  xml += '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\n';
  xml += ' xmlns:o="urn:schemas-microsoft-com:office:office"\n';
  xml += ' xmlns:x="urn:schemas-microsoft-com:office:excel"\n';
  xml += ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\n';
  xml += ' xmlns:html="http://www.w3.org/TR/REC-html40">\n';
  xml += `<Worksheet ss:Name="${sheetName}">\n`;
  xml += '<Table>\n';
  
  // Headers
  xml += '<Row>\n';
  headers.forEach((header) => {
    xml += `<Cell><Data ss:Type="String">${escapeXml(header)}</Data></Cell>\n`;
  });
  xml += '</Row>\n';
  
  // Data rows
  data.forEach((row) => {
    xml += '<Row>\n';
    headers.forEach((header) => {
      const value = row[header];
      const type = typeof value === "number" ? "Number" : "String";
      xml += `<Cell><Data ss:Type="${type}">${escapeXml(String(value || ""))}</Data></Cell>\n`;
    });
    xml += '</Row>\n';
  });
  
  xml += '</Table>\n';
  xml += '</Worksheet>\n';
  xml += '</Workbook>';
  
  const blob = new Blob([xml], { type: "application/vnd.ms-excel" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename.endsWith(".xlsx") ? filename : `${filename}.xlsx`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const escapeXml = (str: string): string => {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
};

/**
 * Export timesheets with detailed format
 */
export const exportTimesheetsToCSV = (timesheets: WeeklyTimesheet[], filename: string) => {
  const headers = [
    "ID",
    "Mitarbeiter",
    "Woche Start",
    "Woche Ende",
    "Status",
    "Einträge",
    "Verifiziert",
    "Erstellt am",
  ];
  
  const rows = timesheets.map((ts) => [
    ts.id,
    ts.user_name,
    ts.week_start,
    ts.week_end,
    ts.status,
    ts.entries.length.toString(),
    ts.signed_pdf_verified ? "Ja" : "Nein",
    ts.created_at || "",
  ]);

  exportToCSV(rows.map((row) => {
    const obj: Record<string, string> = {};
    headers.forEach((header, j) => {
      obj[header] = row[j];
    });
    return obj;
  }), filename, headers);
};

export const exportTimesheetsToJSON = (timesheets: WeeklyTimesheet[], filename: string) => {
  exportToJSON(timesheets, filename.endsWith(".json") ? filename : `${filename}.json`);
};

export const exportTimesheetsToExcel = (timesheets: WeeklyTimesheet[], filename: string) => {
  const data = timesheets.map((ts) => ({
    ID: ts.id,
    Mitarbeiter: ts.user_name,
    "Woche Start": ts.week_start,
    "Woche Ende": ts.week_end,
    Status: ts.status,
    Einträge: ts.entries.length,
    Verifiziert: ts.signed_pdf_verified ? "Ja" : "Nein",
    "Erstellt am": ts.created_at || "",
  }));
  
  exportToExcel(data, filename, "Stundenzettel");
};

