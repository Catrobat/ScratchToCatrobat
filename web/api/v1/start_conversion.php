<?php

//------------------------------------------------------------------------------
// Parameter validation
//------------------------------------------------------------------------------

function dieWithErrorMessage($message) {
    $result = array('success' => false, 'message' => $message, 'data' => array());
    echo json_encode($result);
    exit();
}

if (isset($argv[1])) {
	$_GET['id'] = $argv[1];
}

if (! isset($_GET['id']) || empty($_GET['id'])) {
    error_log("Get: ".print_r($_GET, true));
    dieWithErrorMessage('No project id given!');
}

if (! ctype_digit($_GET['id'])) {
    error_log("Get: ".print_r($_GET, true));
    dieWithErrorMessage('Invalid project id given!');
}

$projectID = intval($_GET['id']);

$projectURL = "http://scratch.mit.edu/projects/" . $projectID . "/";

//------------------------------------------------------------------------------
// Conversion
//------------------------------------------------------------------------------

ignore_user_abort(true);

$outputDir = '../../../data/web_output/';
$outputFiles = glob($outputDir.DIRECTORY_SEPARATOR."*.catrobat");
foreach ($outputFiles as $oldOutputFile) { // iterate files
    if (is_file($oldOutputFile)) {
        unlink($oldOutputFile); // delete file
	}
}

$cid = 0;
$lastCIDFile = $outputDir.'last_conversion_id';
$file = fopen($lastCIDFile, 'a+') or dieWithErrorMessage('Conversion failed! Unable to retrive conversion ID.');
if (flock($file, LOCK_EX)) { // exclusive lock
    fseek($file, 0);
    $oldCid = fgets($file);
    if ($oldCid === false || empty($oldCid)) {
        $oldCid = '0';
    }
    if (! ctype_digit($oldCid)) {
        flock($file, LOCK_UN); // release lock
        fclose($file);
        dieWithErrorMessage('Conversion failed! Unable to retrieve conversion ID.');
    }
    $cid = intval($oldCid) + 1;
    ftruncate($file, 0);
    fwrite($file, $cid);
    flock($file, LOCK_UN); // release lock
    fclose($file);
} else {
    fclose($file);
    dieWithErrorMessage('Conversion failed! Unable to retrieve conversion ID.');
}

//$cmd = '/usr/bin/nohup ~/Development/Desktop/ScratchToCatrobat/run --web '.$cid.' '.$projectURL.' >/dev/null 2>&1 &';
$cmd = '../../../run --web '.$cid.' '.$projectURL.' &';
$sysRV = exec($cmd);

if ($sysRV == 1) {
    dieWithErrorMessage('Conversion failed!');
}

echo json_encode(array(
    'success' => true,
    'message' => 'Conversion started!',
    'data' => array('cid' => $cid)
));
exit();


// $outputFiles = glob($outputDir.DIRECTORY_SEPARATOR."*.catrobat");
// if (($sysRV == 1) || (count($outputFiles) == 0)) {
//     dieWithErrorMessage('Conversion failed!');
// }

// //------------------------------------------------------------------------------
// // Download
// //------------------------------------------------------------------------------

// $zipFile = $outputFiles[0];
// $fileName = basename($zipFile);
// error_log("Zipfile: " . $zipFile . " basename: " . $fileName);

// header("Content-Type: application/catrobat+zip");
// header("Content-Disposition: attachment; filename=$fileName");
// header("Content-Length: " . filesize($zipFile));
// readfile($zipFile);

// if (connection_aborted()) {
//     $temp_files = glob($outputDir . '/{,.}*', GLOB_BRACE);
//     error_log("temp_files to delete: " . print_r($temp_files, true));

//     foreach ($temp_files as $file) { // iterate files
//         if (is_file($file)) {
//             unlink($file); // delete file
// 		}
// 	}
// }
