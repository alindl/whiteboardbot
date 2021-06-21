function block_visible(node) {
    return node.parentElement.parentElement.parentElement.parentElement.style.display === "block";
}

function validateCams() {
    if (document.getElementById("fix_dist_bool") && document.getElementById("crop_bool") ) {
      let cam_blocks = Array.from(document.querySelectorAll('.cam'));
      const fix_dist_bool = Boolean(document.getElementById("fix_dist_bool").checked);
      const crop_bool = Boolean(document.getElementById("crop_bool").checked);

      let distMetrics_fields = Array.from(document.querySelectorAll('input[id$="distMetrics"]'));
      let cropMetrics_fields = Array.from(document.querySelectorAll('input[id$="cropMetrics"]'));
      let resolution_fields = Array.from(document.querySelectorAll('input[id$="resolution"]'));
      let src_fields = Array.from(document.querySelectorAll('select[id$="-src"]'));
      let used_sources = [];
      for (const cam of cam_blocks) {
          if (cam.style.display === "block") {
              let resoRegEx = /^[0-9]+x[0-9]+$/;
              printErrorOrNot(!resoRegEx.test(resolution_fields[cam.id.substring(4)].value), resolution_fields[cam.id.substring(4)]);
              if (fix_dist_bool) {
                  let distRegEx = /^([-+]?[0-9]+\.[0-9]+\s?){3,4}$/;
                  printErrorOrNot(!distRegEx.test(distMetrics_fields[cam.id.substring(4)].value), distMetrics_fields[cam.id.substring(4)]);
              }
              if (crop_bool) {
                  let cropRegEx = /^[0-9]+x[0-9]+([-+]?[0-9]+)?([-+]?[0-9]+)?$/;
                  printErrorOrNot(!cropRegEx.test(cropMetrics_fields[cam.id.substring(4)].value), cropMetrics_fields[cam.id.substring(4)]);
              }
              checkForDuplicates(src_fields[cam.id.substring(4)].selectedOptions[0].value, used_sources, src_fields[cam.id.substring(4)]);
          }
      }
    }
}

function validateMail() {
    let mail_blocks = Array.from(document.querySelectorAll('.mail-entry'));
    let mail_fields = Array.from(document.querySelectorAll('input[id$="-address"]'));
    let used_mails = [];
    for (const mail of mail_blocks) {
        if (mail.style.display === "block") {
            const dupl = checkForDuplicates(mail_fields[mail.id.substring(5)].value, used_mails, mail_fields[mail.id.substring(5)]);
            if (!dupl) {
                let addressRegEx = /^(([^<>()\[\].,;:\s@"]+(\.[^<>()\[\].,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
                printErrorOrNot(!addressRegEx.test(mail_fields[mail.id.substring(5)].value), mail_fields[mail.id.substring(5)]);
            }
        }
    }
}

function validateMac() {
    let btn_blocks = Array.from(document.querySelectorAll('.btn-entry'));
    let mac_fields = Array.from(document.querySelectorAll('input[id$="-mac"]'));
    let used_macs = [];
    for (const btn of btn_blocks) {
        if (btn.style.display === "block") {
            const dupl = checkForDuplicates(mac_fields[btn.id.substring(4)].value, used_macs, mac_fields[btn.id.substring(4)]);
            if (!dupl) {
                let macRegEx = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/;
                printErrorOrNot(!macRegEx.test(mac_fields[btn.id.substring(4)].value), mac_fields[btn.id.substring(4)]);
            }
        }
    }
}



function printErrorOrNot(condition, inputField) {
    let visibility = "none";
    let elem_atts = "form-group has-success";
    if (condition) {
        visibility = "block";
        elem_atts = "form-group has-error";
    }
    inputField.nextElementSibling.style.display = visibility;
    inputField.parentElement.setAttribute("class", elem_atts);
}

function checkForDuplicates(selectedValue, arrayOfUsed, selectField) {
    let dupl = false;
    if (arrayOfUsed.includes(selectedValue)) {
        dupl = true;
    }
    printErrorOrNot(dupl, selectField);
    arrayOfUsed.push(selectedValue);
    return dupl;
}

function checkErrors() {
    return document.getElementsByClassName("has-error").length <= 0;

}

function dark_toggle() {

}


$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})

document.addEventListener("DOMContentLoaded", function () {
    if (window.location.pathname === "/edit") {
      validateCams();
      validateMail();
      if (document.querySelectorAll('input[id$="-mac"]').length > 0) {
        validateMac();
      }
      $("#save-alert").fadeTo(5000, 500).slideUp(500, function(){
        $("#save-alert").slideUp(500);
      });
    }
    timestamp_updater();
    document.addEventListener('submit', function () {
        location.hash = "";
    });
});

window.onload = function() {
    $(".overlay").fadeOut(500);
}
