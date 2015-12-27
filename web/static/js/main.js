// var opts = {
//   lines: 13, // The number of lines to draw
//   length: 28, // The length of each line
//   width: 14, // The line thickness
//   radius: 42, // The radius of the inner circle
//   scale: 1, // Scales overall size of the spinner
//   corners: 1, // Corner roundness (0..1)
//   color: '#000', // #rgb or #rrggbb or array of colors
//   opacity: 0.25, // Opacity of the lines
//   rotate: 0, // The rotation offset
//   direction: 1, // 1: clockwise, -1: counterclockwise
//   speed: 1, // Rounds per second
//   trail: 60, // Afterglow percentage
//   fps: 20, // Frames per second when using setTimeout() as a fallback for CSS
//   zIndex: 2e9, // The z-index (defaults to 2000000000)
//   className: 'spinner', // The CSS class to assign to the spinner
//   top: '50%', // Top position relative to parent
//   left: '50%', // Left position relative to parent
//   shadow: false, // Whether to render a shadow
//   hwaccel: false, // Whether to use hardware acceleration
//   position: 'absolute' // Element positioning
// };
// var target = document.getElementById('foo');
// var spinner = new Spinner(opts).spin(target);

function getProjectIDFromURL(projectURL) {
    if (projectURL == null) {
      return null;
    }
    if (projectURL.indexOf("http://scratch.mit.edu/projects/") == -1 && projectURL.indexOf("https://scratch.mit.edu/projects/") == -1) {
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
    return projectID;
}

function enableSubmitButton() {
  $("#btn-convert").removeAttr("disabled").removeClass("deactivate-button").removeClass("activate-button").addClass("activate-button");
}

function disableSubmitButton() {
  $("#btn-convert").attr("disabled", true).removeClass("deactivate-button").removeClass("activate-button").addClass("deactivate-button");
}

function showErrorMessage(msg) {
  $("#field-url").css("border-color", "#FF0000");
  $("#field-url-validation-result").append($("<div></div>").text(msg).css("color", "#FF0000").css("font-weight", "bold"));
}

function showSuccessMessage(msg) {
  $("#field-url").css("border-color", "#006400");
  $("#field-url-validation-result").append($("<div></div>").html(msg).css("color", "#006400").css("font-weight", "bold"));
}

function updateAndShowProjectDetails(projectID) {
  $("#field-url-validation-result").html("");
  if (projectID == null) {
    showErrorMessage("Invalid URL given!");
    disableSubmitButton();
    $(this).focus();
    return;
  }
  var projectMetadataURL = "https://scratch.mit.edu/api/v1/project/" + projectID + "/?format=json";
  $.getJSON(projectMetadataURL, function(data) {
    var div = $("<div></div>").html("<b>Project:</b> " + data["title"]);
    var projectMetadataDiv = $("<div></div>").append(div);
    showSuccessMessage(projectMetadataDiv);
  }).error(function(event, jqxhr, exception) {
    showErrorMessage("Invalid project?? No metadata available!");
    disableSubmitButton();
    $(this).focus();
  });
  enableSubmitButton();
}

function test() {
  alert('test');
  var data = {
    "cmd": "start",
    "args": {
      "url": "http://scratch.mit.edu/projects/10205819/"
    }
  };
  updater.socket.send(JSON.stringify(data));
}

function init() {
    updater.start();
    window.setTimeout("test();", 3000);
}

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/convertersocket";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            updater.showMessage(JSON.parse(event.data));
        }
    },

    showMessage: function(message) {
        alert(message.msg);
    }
};
