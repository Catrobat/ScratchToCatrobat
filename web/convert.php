<?php

# Settings
//DEFINE('JYTHON_EXE', '/opt/jython27/jython');
DEFINE('JYTHON_EXE', '/Users/r4ll3/Development/Desktop/jython2.7b/bin/jython');
DEFINE('S2C_MAIN', '-m scratchtobat.main');

###########################################

if ((!isset($_FILES["filename"]["tmp_name"]) || empty($_FILES["filename"]["tmp_name"])) && 
      (!isset($_POST['url']) || empty($_POST['url']))) {
	error_log("Files: ".print_r($_FILES, true));
	error_log("Post: ".print_r($_POST, true));
  die("No file selected to convert!");
}

$file_or_url = isset($_POST['url']) ? $_POST['url'] : $_FILES["filename"]["tmp_name"];
//$cmd = JYTHON_EXE.' '.S2C_MAIN.' '.escapeshellcmd($file_or_url).' '.$output_dir;
if (isset($_POST['url'] && strpos($file_or_url, 'http://scratch.mit.edu/projects/') === false) {
	die("Invalid URL given!");
}
$output_dir = '../output/';
$cmd = '../converter '.escapeshellcmd($file_or_url).' '.$output_dir;
$sys_rv = exec($cmd);

$output_files = glob($output_dir.DIRECTORY_SEPARATOR."*.catrobat");
if ($sys_rv == 1 || count($output_files) != 1) {
	die("Conversion failed!");
}

# force download
$zip_file = $output_files[0];
$file_name = basename($zip_file);
error_log("Zipfile: ".$zip_file." basename: ".$file_name);

header("Content-Type: application/catrobat+zip");
header("Content-Disposition: attachment; filename=$file_name");
header("Content-Length: " . filesize($zip_file));

readfile($zip_file);

ignore_user_abort(true);
if (connection_aborted()) {
  $temp_files = glob($output_dir.'/{,.}*', GLOB_BRACE);
	error_log("temp_files to delete: ".print_r($temp_files, true));
  foreach ($temp_files as $file) { // iterate files
		if(is_file($file)) {
			unlink($file); // delete file
		}
	} 
}
