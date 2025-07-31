<?php
/**
 * Installation Script for Schmitz Intralogistik Zeiterfassung
 * Run this script once to initialize the database and install dependencies
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "<h1>Schmitz Intralogistik - Zeiterfassung Installation</h1>";

// Check if Composer is available
if (!file_exists('vendor/autoload.php')) {
    echo "<h2>Step 1: Installing Dependencies</h2>";
    echo "<p>Running composer install...</p>";
    
    if (function_exists('exec')) {
        $output = [];
        $return_var = 0;
        exec('composer install 2>&1', $output, $return_var);
        
        if ($return_var === 0) {
            echo "<p style='color: green;'>✅ Dependencies installed successfully!</p>";
        } else {
            echo "<p style='color: red;'>❌ Error installing dependencies:</p>";
            echo "<pre>" . implode("\n", $output) . "</pre>";
            echo "<p><strong>Manual Installation Required:</strong></p>";
            echo "<p>Please run the following command in the api directory:</p>";
            echo "<code>composer install</code>";
            exit;
        }
    } else {
        echo "<p style='color: orange;'>⚠️ exec() function not available. Please run manually:</p>";
        echo "<code>composer install</code>";
        echo "<p>Then refresh this page.</p>";
        exit;
    }
} else {
    echo "<p style='color: green;'>✅ Dependencies already installed.</p>";
}

// Initialize database
echo "<h2>Step 2: Database Initialization</h2>";

try {
    require_once 'config/database.php';
    
    $database = new Database();
    $database->initializeDatabase();
    
    echo "<p style='color: green;'>✅ Database initialized successfully!</p>";
    echo "<p>Default admin account created:</p>";
    echo "<ul>";
    echo "<li><strong>Email:</strong> admin@schmitz-intralogistik.de</li>";
    echo "<li><strong>Password:</strong> admin123</li>";
    echo "</ul>";
    
} catch (Exception $e) {
    echo "<p style='color: red;'>❌ Database initialization failed:</p>";
    echo "<p>" . $e->getMessage() . "</p>";
    echo "<h3>Please check your database configuration in config/database.php</h3>";
    exit;
}

// Check file permissions
echo "<h2>Step 3: File Permissions Check</h2>";

$writableDirectories = [
    '.',
    'utils',
    'config'
];

$allPermissionsOk = true;
foreach ($writableDirectories as $dir) {
    if (is_writable($dir)) {
        echo "<p style='color: green;'>✅ {$dir}/ is writable</p>";
    } else {
        echo "<p style='color: orange;'>⚠️ {$dir}/ is not writable (may cause issues with logs)</p>";
        $allPermissionsOk = false;
    }
}

if (!$allPermissionsOk) {
    echo "<p><strong>Note:</strong> Some directories are not writable. This may not affect basic functionality but could impact logging.</p>";
}

// Test API endpoints
echo "<h2>Step 4: API Test</h2>";

try {
    // Test database connection
    $db = $database->getConnection();
    $stmt = $db->query("SELECT COUNT(*) as user_count FROM users");
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    
    echo "<p style='color: green;'>✅ Database connection successful</p>";
    echo "<p>Users in database: " . $result['user_count'] . "</p>";
    
} catch (Exception $e) {
    echo "<p style='color: red;'>❌ Database connection test failed:</p>";
    echo "<p>" . $e->getMessage() . "</p>";
}

echo "<h2>Installation Complete!</h2>";
echo "<p style='color: green; font-size: 18px;'>🎉 Your Schmitz Intralogistik Zeiterfassung application is ready!</p>";

echo "<h3>Next Steps:</h3>";
echo "<ol>";
echo "<li>Delete this install.php file for security</li>";
echo "<li>Configure your web server to point to the webapp directory</li>";
echo "<li>Access the application through your web browser</li>";
echo "<li>Login with the admin credentials above</li>";
echo "<li>Configure SMTP settings in the admin panel for email functionality</li>";
echo "</ol>";

echo "<h3>File Structure:</h3>";
echo "<pre>";
echo "webapp/\n";
echo "├── index.html              # Main application\n";
echo "├── assets/\n";
echo "│   ├── css/style.css       # Styling\n";
echo "│   └── js/app.js           # Frontend JavaScript\n";
echo "└── api/                    # Backend API\n";
echo "    ├── index.php           # API router\n";
echo "    ├── config/database.php # Database config\n";
echo "    ├── controllers/        # API controllers\n";
echo "    ├── middleware/         # Authentication\n";
echo "    ├── utils/              # PDF & Email services\n";
echo "    └── vendor/             # Dependencies\n";
echo "</pre>";

echo "<h3>Troubleshooting:</h3>";
echo "<ul>";
echo "<li>If you get database connection errors, check config/database.php</li>";
echo "<li>If emails don't work, configure SMTP in the admin panel</li>";
echo "<li>If PDF generation fails, ensure dompdf is properly installed</li>";
echo "<li>For Apache, ensure mod_rewrite is enabled for clean URLs</li>";
echo "</ul>";

echo "<p><a href='../index.html' style='background: #e90118; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Launch Application</a></p>";
?>