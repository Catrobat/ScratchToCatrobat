<?php

# Settings 

DEFINE('JYTHON_EXE', 'jython');
DEFINE('S2C_MAIN', '..\src\scratchtobat\main.py');


###########################################

function replace_extension($filename, $new_extension) 
{
    $info = pathinfo($filename);
    return $info['dirname'].DIRECTORY_SEPARATOR.$info['filename'] . '.' . $new_extension;
}


if (!file_exists(S2C_MAIN))
{
    die("please configure S2C_MAIN in convert.php (scratchtobat main.py not found!)");
}

if ((!isset($_FILES["filename"]["tmp_name"]) || empty($_FILES["filename"]["tmp_name"])) && 
      (!isset($_POST['url']) || empty($_POST['url'])))
{
    die("No file selected to convert!");
}

$file_or_url = isset($_POST['url']) ? $_POST['url'] : $_FILES["filename"]["tmp_name"];
$zip_file = replace_extension(tempnam( '/tmp' , 's2c' ), 'zip');
$cmd = JYTHON_EXE.' '.S2C_MAIN.' '.escapeshellcmd($file_or_url).' '.$zip_file;
$sys_rv = exec($cmd);
if ($sys_rv == 1 || !file_exists($zip_file))
{
    die("Conversion failed!");
}

# force download
$file_name = basename($zip_file);

header("Content-Type: application/zip");
header("Content-Disposition: attachment; filename=$file_name");
header("Content-Length: " . filesize($zip_file));

readfile($zip_file);

?>