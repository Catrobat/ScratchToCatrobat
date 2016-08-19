var spinnerOptions = {
    lines: 17, // The number of lines to draw
    length: 26, // The length of each line
    width: 12, // The line thickness
    radius: 3, // The radius of the inner circle
    corners: 1, // Corner roundness (0..1)
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    color: '#000', // #rgb or #rrggbb or array of colors
    speed: 1.2, // Rounds per second
    trail: 74, // Afterglow percentage
    shadow: true, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    className: 'spinner', // The CSS class to assign to the spinner
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    top: '50%', // Top position relative to parent in px
    left: '50%' // Left position relative to parent in px
};

var baseProjectURL = "https://scratch.mit.edu/projects/";
var defaultProjectURL = baseProjectURL + "10205819/";

function init() {
  setupUIEventHandlers();
  fetchJobsInfo();
}

jQuery(document).ready(function($) { init(); });

function setupUIEventHandlers() {
  $("#field-url").on("blur", function () {
      updateAndShowProjectDetails(getProjectIDFromURL($(this).val()));
  }).on("keydown", function(e) {
    // if (e.keyCode == 13) {
      updateAndShowProjectDetails(getProjectIDFromURL($(this).val()));
    // }
  });
  $("#download_form").submit(function(event) {
    window.location = $("#download-url").val();
    event.preventDefault();
    return false;
  });
  $("#btn-reconvert").on("click", function () {
    var jobID = $("#download-url").val().split("=")[1].split("&")[0]; /* extract job ID */
    /* assume jobID == scratchProjectID */
    var scratchProjectID = jobID;
    var projectURL = baseProjectURL + scratchProjectID + "/";
    $("#field-url").val(projectURL);
    updateAndShowProjectDetails(scratchProjectID);
    $("#cli-messages").hide();
    $("#web-convert-modal").modal();
    $("#force").val("1");
    $("#converter_form").submit();
    event.preventDefault();
    return false;
  });
  $("#converter_form").submit(function(event) {
    var projectURL = $("#field-url").val();
    $("#field-url").val(""); /* clear field */
    var force = ($("#force").val() == "1");
    $("#force").val("0"); /* reset force field */
    $("#field-url-validation-result").html("");
    disableSubmitButton();
    disableDownloadButton();
    $("#btn-download").hide();
    disableReconvertButton();
    $("#btn-reconvert").hide();
    var consoleLayer = $("#console-container")
    consoleLayer.hide();
    $("#qrcode").hide();
    $("#download-url").val("");
    $("#progress-bar").attr("aria-valuenow", "0").css("width", "0%");
    $("#progress").text("0%");
    $("#status").text("Sending request...");
    $("#loading-animation").show();
    var projectID = getProjectIDFromURL(projectURL);
    if (projectID != null) { /* check if project URL is valid! */
      $("#loading-animation-content").html("");
      var spinner = new Spinner(spinnerOptions).spin(document.getElementById("loading-animation-content"));
      consoleLayer.children().each(function () { $(this).hide(); }); /* hide all consoles */
      $(this).hide();
      /* TODO: error handler as another callback! */
      startConversion(projectURL, force, function(downloadURL) {
        enableSubmitButton();
        showSuccessMessage("Conversion finished!");
        consoleLayer.hide();
        $("#download-url").val(downloadURL);
        $("#btn-download").show();
        $("#btn-reconvert").show();
        $("#loading-animation-content").html("");
        $("#loading-animation").hide();
        $("#qrcode").children().remove();
        $("#qrcode").show();
        var qrcode = new QRCode(document.getElementById("qrcode"), { width: 200, height: 200 });
        qrcode.makeCode(downloadURL);
        enableDownloadButton();
        enableReconvertButton();
      });
    } else {
      $("#loading-animation").hide();
      showErrorMessage("Invalid URL given!");
      $(this).focus();
      event.preventDefault();
    }
    return false;
  });
  $("#select_form").submit(function(event) {
    event.preventDefault();
    return false;
  });
  $("#btn-show-url-input").click(function() {
    $("#field-url").val(defaultProjectURL);
    updateAndShowProjectDetails(getProjectIDFromURL(defaultProjectURL));
    $("#web-convert-modal").modal();
    enableSubmitButton();
    disableDownloadButton();
    disableReconvertButton();
    $("#console-container").hide();
    $("#qrcode").hide();
    $("#btn-download").hide();
    $("#btn-reconvert").hide();
    $("#loading-animation").hide();
    $("#converter_form").show();
    $("#field-url").focus();
  });
  $("#btn-show-upload-input").click(function() {
    alert("This feature is coming soon!");
    /*$("#upload-convert-modal").modal();*/
  });
}
