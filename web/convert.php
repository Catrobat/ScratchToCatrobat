<?php

//------------------------------------------------------------------------------
// Parameter validation
//------------------------------------------------------------------------------

if (isset($argv[1])) {
	$_POST['url'] = $argv[1];
}

$tmpNameNotGiven = (! isset($_FILES["filename"]["tmp_name"])
                 || empty($_FILES["filename"]["tmp_name"]));
$URLNotGiven = (! isset($_POST['url']) || empty($_POST['url']));

if ($tmpNameNotGiven && $URLNotGiven) {
    error_log("Files: ".print_r($_FILES, true));
    error_log("Post: ".print_r($_POST, true));
    die("No file selected to convert!");
}

$fileOrURL = isset($_POST['url']) ? $_POST['url'] : $_FILES["filename"]["tmp_name"];

if (isset($_POST['url'])
&& strpos($fileOrURL, 'http://scratch.mit.edu/projects/') === false
&& strpos($fileOrURL, 'https://scratch.mit.edu/projects/') === false
) {
	die("Invalid URL given!");
}


//------------------------------------------------------------------------------
// Conversion
//------------------------------------------------------------------------------

ignore_user_abort(true);

$t = microtime(true);
$micro = sprintf("%06d",($t - floor($t)) * 1000000);
$d = new DateTime(date('Y-m-d H:i:s.'.$micro, $t));
$outputDir = '../data/web_output/'.$d->format("Y-m-d_H.i.s.u").'/';

if (! file_exists('path/to/directory')) {
    if (@mkdir($outputDir, 0777, true) === false) {
        die("Conversion failed! No permissions.");
    }
} else {
    die("Conversion failed! Resource already exists.");
}

// $outputFiles = glob($outputDir.DIRECTORY_SEPARATOR."*.catrobat");
// foreach ($outputFiles as $oldOutputFile) { // iterate files
//     if (is_file($oldOutputFile)) {
//         unlink($oldOutputFile); // delete file
// 	}
// }

$cmd = '../run '.escapeshellcmd($fileOrURL).' '.$outputDir;
$sysRV = exec($cmd);

$outputFiles = glob($outputDir.DIRECTORY_SEPARATOR."*.catrobat");
if (($sysRV == 1) || (count($outputFiles) == 0)) {
	die("Conversion failed!");
}


//------------------------------------------------------------------------------
// Download
//------------------------------------------------------------------------------

$zipFile = $outputFiles[0];
$fileName = basename($zipFile);
error_log("Zipfile: " . $zipFile . " basename: " . $fileName);

header("Content-Type: application/catrobat+zip");
header("Content-Disposition: attachment; filename=$fileName");
header("Content-Length: " . filesize($zipFile));
readfile($zipFile);
