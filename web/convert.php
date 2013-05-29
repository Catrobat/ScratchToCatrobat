<?php

# Settings 

DEFINE('JYTHON_EXE', 'jython');
DEFINE('S2C_MAIN', '..\src\scratchtobat\main.py');


###########################################

function replace_extension($filename, $new_extension) 
{
    $info = pathinfo($filename);
    return $info['filename'] . '.' . $new_extension;
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


echo $_FILES["filename"]["tmp_name"];
$tmpfile =  replace_extension(tempnam( '/tmp' , 's2c' ), 'zip');
echo $tmpfile;

exit;

$cmd = JYTHON_EXE.' '.S2C_MAIN;
system($cmd);


#dummy download 
$yourfile = "hello.sb2.zip";

$file_name = basename($yourfile);

header("Content-Type: application/zip");
header("Content-Disposition: attachment; filename=$file_name");
header("Content-Length: " . filesize($yourfile));

readfile($yourfile);

?>