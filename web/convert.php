<?php

//------------------------------------------------------------------------------
// Parameter validation
//------------------------------------------------------------------------------

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
&& strpos($fileOrURL, 'https://scratch.mit.edu/projects/') === false)
{
	die("Invalid URL given!");
}


//------------------------------------------------------------------------------
// Conversion
//------------------------------------------------------------------------------

ignore_user_abort(true);

$outputDir = '../data/web_output/';
$outputFiles = glob($outputDir.DIRECTORY_SEPARATOR."*.catrobat");
foreach ($outputFiles as $oldOutputFile) { // iterate files
    if (is_file($oldOutputFile)) {
        unlink($oldOutputFile); // delete file
	}
}

$cmd = '../run.py ' . escapeshellcmd($fileOrURL) . ' ' . $outputDir;
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

if (connection_aborted()) {
    $temp_files = glob($outputDir . '/{,.}*', GLOB_BRACE);
    error_log("temp_files to delete: " . print_r($temp_files, true));

    foreach ($temp_files as $file) { // iterate files
        if (is_file($file)) {
            unlink($file); // delete file
		}
	}
}
