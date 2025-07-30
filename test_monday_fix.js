// Test the corrected Monday calculation
function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Get Monday of current week
    return new Date(d.setDate(diff));
}

function formatDateForInput(date) {
    return date.toISOString().split('T')[0];
}

function getAvailableMondays() {
    const mondays = [];
    const today = new Date();
    const currentMonday = getMonday(today);
    
    // Generate Mondays: from 4 weeks ago to 8 weeks in the future
    for (let i = -4; i <= 8; i++) {
        const monday = new Date(currentMonday);
        monday.setDate(currentMonday.getDate() + (i * 7));  // Add i weeks
        
        // Calculate correct calendar week
        const yearStart = new Date(monday.getFullYear(), 0, 1);
        const weekNumber = Math.ceil(((monday - yearStart) / (7 * 24 * 60 * 60 * 1000)) + 1);
        
        mondays.push({
            value: formatDateForInput(monday),
            label: `${monday.toLocaleDateString('de-DE')} (KW ${weekNumber})`
        });
    }
    
    return mondays;
}

function testSpecificCase() {
    console.log("=== TESTING MONDAY CALCULATION ===");
    console.log("");
    
    // Test today
    const today = new Date();
    const mondayToday = getMonday(today);
    console.log(`Today: ${today.toLocaleDateString('de-DE')}`);
    console.log(`Monday of this week: ${mondayToday.toLocaleDateString('de-DE')}`);
    console.log("");
    
    // Test specific case: July 7, 2025 (Monday)
    const july7 = new Date('2025-07-07'); // Monday
    const mondayFromJuly7 = getMonday(july7);
    console.log(`Test date: ${july7.toLocaleDateString('de-DE')} (${['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'][july7.getDay()]})`);
    console.log(`Monday calculation result: ${mondayFromJuly7.toLocaleDateString('de-DE')}`);
    
    if (july7.getTime() === mondayFromJuly7.getTime()) {
        console.log("✅ SUCCESS: July 7, 2025 correctly returns July 7, 2025");
    } else {
        console.log("❌ FAILURE: July 7, 2025 should return July 7, 2025");
    }
    console.log("");
    
    // Test Sunday before (July 6, 2025)
    const july6 = new Date('2025-07-06'); // Sunday
    const mondayFromJuly6 = getMonday(july6);
    console.log(`Test date: ${july6.toLocaleDateString('de-DE')} (${['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'][july6.getDay()]})`);
    console.log(`Monday calculation result: ${mondayFromJuly6.toLocaleDateString('de-DE')}`);
    
    if (mondayFromJuly6.toDateString() === july7.toDateString()) {
        console.log("✅ SUCCESS: July 6, 2025 (Sunday) correctly returns July 7, 2025 (Monday)");
    } else {
        console.log("❌ FAILURE: July 6, 2025 (Sunday) should return July 7, 2025 (Monday)");
    }
    console.log("");
    
    // Show available Mondays
    const availableMondays = getAvailableMondays();
    console.log("Available Monday options:");
    availableMondays.slice(0, 5).forEach((monday, index) => {
        console.log(`${index + 1}. ${monday.label}`);
    });
}

testSpecificCase();
