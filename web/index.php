<?php
function valueForConfigKey($key, $rawConfigContent) {
	$start = strpos($rawConfigContent, $key);
	$temp = substr($rawConfigContent, $start);
	$end = strpos($temp, "\n");
	$start = strlen($key);
	$end = $end - $start;
	return trim(substr($temp, $start, $end));
}

$rawConfigContent = file_get_contents('../config/default.ini');
$versionNumber = valueForConfigKey('version:', $rawConfigContent);
$buildName = valueForConfigKey('build_name:', $rawConfigContent);
$buildNumber = valueForConfigKey('build_number:', $rawConfigContent);
?><!DOCTYPE html>
<html lang="en">
<head>
  <title>Scratch to Catrobat Converter</title>
  <meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
  <link rel="shortcut icon" href="./images/logo/favicon.png" />
  <link rel="stylesheet" href="./css/main.css" media="screen"/>
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
  <script type="text/javascript" src="./js/qrcode.min.js"></script>
  <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
  <script type="text/javascript" src="./js/spin.min.js"></script>
  <script type="text/javascript" src="./js/main.js"></script>
  <script>
    jQuery(document).ready(function($) {
  		$("#btn-convert").removeClass("deactivate-button").addClass("activate-button");
      init();
  		$("#version-link").click(function() {
  			alert("Version: <?php echo $versionNumber; ?>\nBuild: <?php echo $buildName; ?> (<?php echo $buildNumber; ?>)");
  			return false;
  		});
  		$("#field-url").on("blur", function () {
        updateAndShowProjectDetails(getProjectIDFromURL($(this).val()));
      }).on("keydown", function(e) {
        // if (e.keyCode == 13) {
          updateAndShowProjectDetails(getProjectIDFromURL($(this).val()));
        // }
  		});
      // $("#converter_form").submit(function(event) {
      //   var projectConversionURL = "/api/v1/start_conversion.php?id={0}";
      //   var projectID = getProjectIDFromURL($("#field-url").val());
      //   $("#field-url-validation-result").html("");
      //   if (projectID == null) {
      //     showErrorMessage("Invalid URL given!");
      //     disableSubmitButton();
      //     $(this).focus();
      //     event.preventDefault();
      //     return false;
      //   }
      //   $.getJSON(projectConversionURL.replace("{0}", projectID), function(data) {

      //   });
      //   event.preventDefault();
      //   return false;
      // });
      $("#select_form").submit(function(event) {
        event.preventDefault();
        return false;
      });
      $("#btn-show-url-input").click(function() {
        updateAndShowProjectDetails(getProjectIDFromURL($("#field-url").val()));
        $("#web-convert-modal").modal();
        $("#field-url").focus();
        // $("#qrcode").children().remove();
        // var qrcode = new QRCode(document.getElementById("qrcode"), {
        //   width : 200,
        //   height : 200
        // });
        // qrcode.makeCode($("#field-url").val());
      });
      $("#btn-show-upload-input").click(function() {
        $("#upload-convert-modal").modal();
      });
    });
  </script>
</head>
<body>
  <div class="ribbon">
    <a href="#" id="version-link">beta</a>
  </div>
  <div id="wrapper">
    <header>
      <nav>
        <div id="header-top">
          <div><a href="https://share.catrob.at/pocketcode/help">Tutorials</a></div>
          <div><a href="http://www.catrobat.org">About</a></div>
        </div>
        <div id="header-left">
          <div id="logo">
            <a href="/pocketcode/">
              <img src="/images/logo/logo_text.png" alt="Pocket Code Logo" />
            </a>
          </div>
        </div>
      </nav>
    </header>

    <article>
      <div id="select-page" style="text-align:center;">
        <p>&nbsp;</p>
        <h2>Convert Scratch projects to Pocket Code programs</h2>
        <p>Quickly turn your Scratch desktop projects into full-fledged mobile Pocket Code programs</p>
        <p>&nbsp;</p>
        <div>
          <form id="select_form" action="#">
            <div><input type="submit" name="btn-show-url-input" id="btn-show-url-input" value="Enter URL" class="convert-button activate-button" /></div>
            <div style="margin:20px;margin-bottom:0;font-size:25px;font-weight:bold;">or</div>
            <div><input type="submit" name="btn-show-upload-input" id="btn-show-upload-input" value="Upload" class="convert-button activate-button" /></div>
          </form>
        </div>
      </div>
    </article>
    <aside id="modal-pages">
      <section id="web-convert-modal-section">
        <div id="web-convert-modal" class="modal fade" role="dialog">
          <div class="modal-dialog modal-lg" style="min-width:350px;max-width:700px;">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal">&times;</button>
                <h4 class="modal-title">Convert Scratch projects to Catrobat</h4>
                <div>Quickly turn your Scratch desktop projects into full-fledged mobile Catrobat projects</div>
              </div>
              <div class="modal-body">
                <div style="text-align:center;">
                  <form id="converter_form" action="convert.php" method="post" enctype="multipart/form-data">
                    <p style="font-size:18px;">Enter a Scratch project URL ...</p>
                    <div class="input-field">
                      <input type="text" id="field-url" name="url" value="http://scratch.mit.edu/projects/10205819/" class="clearable" />
                    </div>
                    <div id="field-url-validation-result"></div>
                    <!-- <div id="qrcode" style="width:200px;height:200px;margin-top:15px;"></div> -->
                    <input type="submit" name="submit" id="btn-convert" value="Convert" class="convert-button deactivate-button" />
                  </form>
                </div>
                <div class="separator-line"></div>
                <div>
                  <h2>How it works</h2>
                  <div>
                    <ol>
                      <li>Enter the project URL in the input field above and hit the "Convert" button.</li>
                      <li>After the conversion has finished a QR-Code will be shown.</li>
                      <li>Install and open the PocketCode app on your <a href="https://play.google.com/store/apps/details?id=org.catrobat.catroid" target="_blank">Android</a> or iOS device (coming soon).</li>
                      <li>Now hold your device over the QR Code so that it's clearly visible within your smartphone's screen.</li>
                      <li>Your project should subsequently open on your mobile device.</li>
                      <li>That's it. :)</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section id="upload-convert-modal-section">
        <div id="upload-convert-modal" class="modal fade" role="dialog">
          <div class="modal-dialog modal-lg" style="min-width:350px;max-width:700px;">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal">&times;</button>
                <h4>Convert Scratch projects to Catrobat</h4>
                <div>Please select your locally stored Scratch project (.sb2 file) and hit the <i>Convert</i> button</div>
              </div>
              <div class="modal-body">
                <div style="text-align:center;">
                  <form id="converter_form" action="convert.php" method="post" enctype="multipart/form-data">
                    <div class="input-field" style="margin-left:auto;margin-right:auto;width:200px;">
                      <input type="file" id="field-filename" name="filename" class="size-large input-search" />
                    </div>
                    <input type="submit" name="submit" id="btn-convert" value="Convert" class="convert-button activate-button" />
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </aside>
  </div>
<!--
  <footer>
    <p>&nbsp;</p>
    <div id="footer-menu" class="footer-padding">
      <div>&copy; Copyright 2014 - 2015 Catrobat Team</div>
    </div>
    <p>&nbsp;</p>
    <p>&nbsp;</p>
  </footer>
 -->
</body>
</html>
