<?php
/**
 * Pix42 - Usage Analytics
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);

    // GDPR-compliant validation: app_version + timestamp required
    if (!$data || !isset($data['app_version']) || !isset($data['timestamp'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid data: app_version and timestamp required']);
        exit;
    }

    // Monthly rotation: usage_data_YYYY-MM.jsonl
    $month = date('Y-m');
    $filename = "usage_data_{$month}.jsonl";

    if (file_put_contents($filename, json_encode($data) . "\n", FILE_APPEND | LOCK_EX)) {
        echo json_encode(['status' => 'success']);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to save']);
    }

} elseif ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // GET is blocked by .htaccess for security
    http_response_code(403);
    echo json_encode(['error' => 'Access denied']);

} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>
