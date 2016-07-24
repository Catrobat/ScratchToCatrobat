// fetch jobs info if client ID is set
function fetchJobsInfo() {
  // fetch jobs info if client ID is set
  socketHandler.openedSockedCallback = function() {
    if (typeof(Storage) !== "undefined") {
      socketHandler.clientID = localStorage.getItem("clientID");
    }
    var data = { "cmd": "set_client_ID", "args": { "clientID": socketHandler.clientID } };
    socketHandler.socket.send(JSON.stringify(data));
  };
  socketHandler.start();
}

function startConversion(url, force, finishedConversionCallback) {
  socketHandler.projectID = getProjectIDFromURL(url);
  socketHandler.finishedConversionCallback = finishedConversionCallback;
  var data = {
    "cmd": "schedule_job",
    "args": {
      "clientID": socketHandler.clientID,
      "jobID": socketHandler.projectID,
      "force": force
    }
  };
  socketHandler.socket.send(JSON.stringify(data));
}

var socketHandler = {
    projectID: null,
    socket: null,
    clientID: null,
    finishedConversionCallback: null,
    openedSockedCallback: null,
    lastProgress: null,
    lastProgressCheck: null,
    averageProgressSpeed: null,
    progressStart: null,

    start: function() {
        // TODO: lock and check if opened!
        if (socketHandler.socket != null) {
          socketHandler.openedSockedCallback();
          return;
        }
        var websocketProtocol = "ws://";
        if (window.location.protocol == "https:") {
          websocketProtocol = "wss://";
        }
        var websocketURL = websocketProtocol + location.host + "/convertersocket";
        socketHandler.socket = new WebSocket(websocketURL);
        socketHandler.socket.onopen = function() { socketHandler.openedSockedCallback(); };
        socketHandler.socket.onmessage = function(event) { socketHandler.receiveMessageHandler(event); }
    },

    receiveMessageHandler: function(event) {
      var result = JSON.parse(event.data);
      var notificationTypes = {
        "ERROR": 0,
        "JOB_FAILED": 1,
        "JOB_RUNNING": 2,
        "JOB_ALREADY_RUNNING": 3,
        "JOB_READY": 4,
        "JOB_OUTPUT": 5,
        "JOB_PROGRESS": 6,
        "JOB_FINISHED": 7,
        "JOB_DOWNLOAD": 8,
        "JOBS_INFO": 9,
        "CLIENT_ID": 10
      };

      // ERROR: { "msg" }
      if (result.type == notificationTypes["ERROR"]) {
        alert("ERROR: " + result.data["msg"]);
        return;
      }

      // JOB_FAILED: { "jobID" }
      if (result.type == notificationTypes["JOB_FAILED"]) {
        if (result.data["jobID"] != socketHandler.projectID) {
          return;
        }
        if ($("#console-container").is(':visible') == false) {
          $("button.close").click();
        } else {
          $("#loading-animation-content").html("");
          $("#loading-animation").hide();
        }
        $("#status").text("Job failed!");
        return;
      }

      // JOB_RUNNING: { "jobID" }
      if (result.type == notificationTypes["JOB_RUNNING"]) {
        $("#status").text("Job running...");
      }

      // JOB_ALREADY_RUNNING: { "jobID" }
      if (result.type == notificationTypes["JOB_ALREADY_RUNNING"]) {
        $("#status").text("Job already running...");
      }

      // JOB_READY: { "jobID" }
      if (result.type == notificationTypes["JOB_READY"]) {
        $("#status").text("Waiting for worker to process this job...");
      }

      // JOB_OUTPUT: { "jobID", "line" }
      if (result.type == notificationTypes["JOB_OUTPUT"]) {
        var consoleLayer = $("#console-container");
        var projectConsoleID = "console_" + socketHandler.projectID;
        /* if no console for this project already exists create one */
        var projectConsole = null;
        if (consoleLayer.find("#"+projectConsoleID).length == 0) {
          projectConsole = $("<div></div>").attr("id", projectConsoleID);
          consoleLayer.append(projectConsole);
        } else {
          projectConsole = $("#"+projectConsoleID);
        }
        var consoleForMessage = null;
        var projectIDForMessage = result.data["jobID"];
        if (socketHandler.projectID == projectIDForMessage) {
          /* case: message is sent to console of this project */
          projectConsole.show(); /* show console of this project */
          consoleLayer.show();
          consoleForMessage = projectConsole;
        } else {
          /* case: message is sent to console of other project */
          var messageConsoleID = "console_" + projectIDForMessage.projectID;
          /* if no console for this message already exists create one */
          if (consoleLayer.find("#"+messageConsoleID).length == 0) {
            consoleForMessage = $("<div></div>").attr("id", projectIDForMessage);
            consoleLayer.append(consoleForMessage);
          } else {
            consoleForMessage = $("#"+messageConsoleID);
          }
          consoleForMessage.hide();
        }
        var lines = result.data["lines"];
        for (var i = 0; i < lines.length; ++i) {
          var progressMsgLine = $("<div></div>").addClass("console-message");
          progressMsgLine.text(lines[i]);
          consoleForMessage.append(progressMsgLine);
        }
        var height = consoleLayer[0].scrollHeight;
        consoleLayer.scrollTop(height);
        return;
      }

      // JOB_PROGRESS: { "jobID", "progress" }
      if (result.type == notificationTypes["JOB_PROGRESS"]) {
        var progress = result.data["progress"];
        var roundedProgress = Math.round(progress);
        $("#progress-bar").attr("aria-valuenow", progress).css("width", roundedProgress + "%");
        $("#progress").text(progress + "%");
        var now = new Date();
        if ((socketHandler.lastProgress == null) || (socketHandler.lastProgressCheck == null)) {
          /*$("#status").text("Calculating remaining time...");*/
          socketHandler.progressStart = now;
        } else {
          var timeIntervalInMS = (now - socketHandler.lastProgressCheck);
          var timeElapsedInMS = (now - socketHandler.progressStart);
          var lastSpeed = (progress - socketHandler.lastProgress) / timeIntervalInMS;
          /* based on: http://stackoverflow.com/a/3841706 */
          var SMOOTHING_FACTOR = 0.03;
          if (socketHandler.averageProgressSpeed != null) {
            socketHandler.averageProgressSpeed = SMOOTHING_FACTOR * lastSpeed + (1-SMOOTHING_FACTOR) * socketHandler.averageProgressSpeed;
          } else {
            socketHandler.averageProgressSpeed = lastSpeed;
          }
          var etaInMS = (100.0 - progress)/socketHandler.averageProgressSpeed;
          var etaInS = etaInMS/1000;
          /*
          if (etaInS > 60*60) {
            $("#status").text("Approximately " + Math.round(etaInS/(60*60)) + " hours remaining...");
          } else if (etaInS > 60) {
            $("#status").text("Approximately " + Math.round(etaInS/60) + " minutes remaining...");
          } else {
            $("#status").text("Approximately " + Math.round(etaInS) + " seconds remaining...");
          }
          */
          //var estimatedEndTime = now + estimatedRemaining;
        }
        socketHandler.lastProgress = progress;
        socketHandler.lastProgressCheck = now;
      }

      // JOB_FINISHED: { "jobID" }
      if (result.type == notificationTypes["JOB_FINISHED"]) {
        $("#status").text("Job finished!");
      }

      // JOB_DOWNLOAD: { "jobID", "url" }
      if (result.type == notificationTypes["JOB_DOWNLOAD"]) {
        if (result.data["jobID"] != socketHandler.projectID) {
          return;
        }
        var download_url = location.protocol + "//" + location.host + result.data["url"];
        if (socketHandler.finishedConversionCallback != null) {
          socketHandler.finishedConversionCallback(download_url);
        }
        return;
      }

      // JOBS_INFO: { "jobsInfo" }
      if (result.type == notificationTypes["JOBS_INFO"]) {
        var statusText = ["Ready", "Running", "Finished", "Failed"];
        $("#jobs_info_table").children().remove();
        for (var index in result.data["jobsInfo"]) {
          var jobInfo = result.data["jobsInfo"][index];
          var tr = $("<tr></tr>");
          var jobID = jobInfo.ID;
          var statusLink = $("<a></a>").attr("href", "#").attr("id", "job_ID[" + jobInfo.jid + "]").addClass("job_link").text(statusText[jobInfo.status]);
          tr.append($("<td></td>").append(statusLink));
          var scratchProjectLink = $("<a></a>").attr("href", jobInfo.url).attr("target", "_blank").text(jobInfo.url);
          var scratchProjectLinkLayer = $("<div></div>").append(scratchProjectLink);
          tr.append($("<td></td>").append($("<div></div>").text(jobInfo.title)).append(scratchProjectLinkLayer));
          tr.append($("<td></td>").text(jobInfo.progress + "%"));
          $("#jobs_info_table").append(tr);
        }
        $("a.job_link").on("click", function() {
          var jobID = $(this).attr("id").split("[")[1].split("]")[0]; /* extract job ID */
          /* assume jobID == scratchProjectID */
          var scratchProjectID = jobID;
          var projectURL = baseProjectURL + scratchProjectID + "/";
          $("#field-url").val(projectURL);
          updateAndShowProjectDetails(scratchProjectID);
          $("#cli-messages").hide();
          $("#web-convert-modal").modal();
          $("#converter_form").submit();
          event.preventDefault();
          return false;
        });
        return;
      }

      // CLIENT_ID: { "clientID" }
      if (result.type == notificationTypes["CLIENT_ID"]) {
        socketHandler.clientID = result.data["clientID"];
        if (typeof(Storage) !== "undefined") {
          localStorage.setItem("clientID", socketHandler.clientID);
        }
      }

    }

};
