/* helpers */
function createGetJSONCallback(callback, info) {
   return function(data) { callback(data, info); };
}

function fetchProjectDetails(projectID, info, successHandler, errorHandler) {
  var projectMetadataURL = "https://scratch.mit.edu/api/v1/project/" + projectID + "/?format=json";
  $.getJSON(projectMetadataURL, createGetJSONCallback(successHandler, info)).error(errorHandler);
}

function getProjectIDFromURL(projectURL) {
    if (projectURL == null) {
      return null;
    }
    projectURL = projectURL.replace("http://", "https://");
    if (projectURL.indexOf("https://scratch.mit.edu/projects/") == -1) {
      return null;
    }
    var urlParts = projectURL.split("/");
    if (urlParts.length < 5) {
      return null;
    }
    var projectID = urlParts[urlParts.length - 1];
    if (projectID == "") {
      projectID = urlParts[urlParts.length - 2];
    }
    return parseInt(projectID);
}

function updateAndShowProjectDetails(projectID) {
  $("#field-url-validation-result").html("");
  if (projectID == null) {
    showErrorMessage("Invalid URL given!");
    disableSubmitButton();
    $(this).focus();
    return;
  }
  enableSubmitButton();
  fetchProjectDetails(projectID, null, function(data, info) {
    var div = $("<div></div>").html("<b>Project:</b> " + data["title"]);
    var projectMetadataDiv = $("<div></div>").append(div);
    showSuccessMessage(projectMetadataDiv);
  }, function(event, jqxhr, exception) {
    showErrorMessage("Invalid project?? No metadata available!");
    disableSubmitButton();
    $(this).focus();
  });
}

/* UI helpers */
function enableSubmitButton() {
  $("#btn-convert").removeAttr("disabled").removeClass("deactivate-button").removeClass("activate-button").addClass("activate-button");
}

function disableSubmitButton() {
  $("#btn-convert").attr("disabled", true).removeClass("deactivate-button").removeClass("activate-button").addClass("deactivate-button");
}

function enableDownloadButton() {
  $("#btn-download").removeAttr("disabled").removeClass("deactivate-button").removeClass("activate-button").addClass("activate-button");
}

function disableDownloadButton() {
  $("#btn-download").attr("disabled", true).removeClass("deactivate-button").removeClass("activate-button").addClass("deactivate-button");
}

function enableReconvertButton() {
  $("#btn-reconvert").removeAttr("disabled").removeClass("deactivate-button").removeClass("activate-button").addClass("activate-button");
}

function disableReconvertButton() {
  $("#btn-reconvert").attr("disabled", true).removeClass("deactivate-button").removeClass("activate-button").addClass("deactivate-button");
}

function showErrorMessage(msg) {
  $("#field-url").css("border-color", "#FF0000");
  $("#field-url-validation-result").append($("<div></div>").text(msg).css("color", "#FF0000").css("font-weight", "bold"));
}

function showSuccessMessage(msg) {
  $("#field-url").css("border-color", "#006400");
  $("#field-url-validation-result").append($("<div></div>").html(msg).css("color", "#006400").css("font-weight", "bold"));
}
