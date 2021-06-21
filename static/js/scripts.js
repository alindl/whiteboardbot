// TODO Toggle visibility instead of setting the value over and over again like a lunatic

function partVisibility(number_of_things, num_value, prefix, limit) {
    if (document.getElementById(number_of_things)) {
      const num_things = Number(document.getElementById(number_of_things).value);
      for (let num = 0; num < limit; num++) {
          const thing = document.getElementById(prefix + num);
          let visibility = "none";
          if (num < num_things) {
              visibility = "block";
          }
          thing.style.display = visibility;
      }
      const bubble = document.querySelector(num_value);
      bubble.textContent = num_things;
      if (document.querySelector(num_value + "_2")) {
          const header_num = document.querySelector(num_value + "_2");
          header_num.textContent = num_things;
      }
      const newVal = Number(((num_things - 1) * 100) / (limit - 1));
      bubble.style.left = `calc(${newVal}% + (${27 - newVal * 0.56}px))`;
    }
}

function checkActivation(checkboxName, className) {
    const check_bool = getActivationValue(checkboxName);
    const fix_elems = document.getElementsByClassName(className);
    if (fix_elems) {
        for (const c of fix_elems) {
            let visibility = "none";
            if (check_bool) {
                visibility = "block";
            }
            c.style.display = visibility;
        }
    }
}

function checkCamFields() {
    const check_dist = getActivationValue("fix_dist_bool");
    const check_crop = getActivationValue("crop_bool");
    const fix_elems = document.getElementsByClassName("inner-cam");
    if (fix_elems) {
        for (const c of fix_elems) {
            let dist_visible = "none";
            let crop_visible = "none";
            if (check_dist) {
                dist_visible = "block";
            }
            if (check_crop) {
                crop_visible = "block";
            }
            c.getElementsByClassName("form-group")[2].style.display = dist_visible;
            c.getElementsByClassName("form-group")[3].style.display = crop_visible;
        }
    }
}

function requestActivation() {
    const slack_bool = getActivationValue("slack_bool");
    const request_bool = getActivationValue("request_bool");
    let slack_request_elem = document.getElementsByClassName("slack-request")[0];
    let slack_channel = document.getElementById("slack-flex")
    if (slack_request_elem) {
        let visibility = "none";
        let remove_class = "col-md-6";
        let add_class = "col-md-12";
        if (slack_bool && request_bool) {
            visibility = "block";
            [remove_class, add_class] = [add_class, remove_class];
        }
        slack_request_elem.style.display = visibility;
        slack_channel.classList.remove(remove_class);
        slack_channel.classList.add(add_class);
    }
}

function addOption(value, text) {
    let new_option = document.createElement("option");
    new_option.setAttribute('value', value);
    let t = document.createTextNode(text);
    new_option.appendChild(t);
    return new_option;
}

function getActiveActions() {
    // We can't go deeper, need the display block
    const mail_entries = document.getElementsByClassName('mail-entry');
    const mail_bool = getActivationValue("mail_bool");
    let slack_bool = true;
    if (document.getElementById("slack_bool") !== null) {
      slack_bool = getActivationValue("slack_bool");
    }
    // These are ALL button Dropdown fields
    // const btn_entries = document.querySelectorAll('div.btn-entry > div > fieldset > div > select');
    const entries = document.querySelectorAll('option');
    const options = Array.from(entries);

    options.forEach(entry => {
        entry.style.display = "block"
    })
    for (const option of entries) {
        if (!slack_bool && option.value === "slack") {
            option.style.display = "none";
            option.removeAttribute('selected');
        }
        if (!mail_bool && (option.value === "all_mail" || option.value.startsWith("mail_"))) {
            option.style.display = "none";
            option.removeAttribute('selected');
        } else {
            // What the hell was I thinking there
            for (const mailblock of mail_entries) {
                if (mailblock.style.display === "none" && option.value === mailblock.id) {
                    option.style.display = "none";
                    option.removeAttribute('selected');
                }
            }
        }
    }
}

function resetFields(formname, tagname) {
    let fields = document.getElementsByClassName(formname);
    for (const d of fields) {
        let fix_elems = d.getElementsByTagName(tagname);
        if (d.style.display === "none") {
            for (const c of fix_elems) {
                c.value = c.defaultValue;
            }
        }
    }
}

function getActivationValue(field) {
    if (document.getElementById(field)) {
      return Boolean(document.getElementById(field).checked);
    }
}

function addItem(item){
    document.getElementById(item).value++;
}
function rmItem(item){
    document.getElementById(item).value--;
}

document.addEventListener("DOMContentLoaded", function () {
    partVisibility("num_of_bttns", "#btn_val", "btn_", 10);
    if (window.location.pathname === "/edit") {
      partVisibility("num_of_cams", "#cam_val", "cam_", 10);
      partVisibility("num_of_mails", "#mail_val", "mail_", 41);
      checkCamFields();
      if (document.getElementById("slack_bool") !== null) {
        checkActivation("slack_bool", "slack");
        requestActivation();
      }
      if (document.getElementById("mail_bool") !== null) {
        checkActivation("mail_bool", "mail");
      }
      checkActivation("audio_bool", "audio");
      getActiveActions();
    }

$(document).ready(function () {
    if(location.hash != null && location.hash != ""){
        $('.collapse').removeClass('in');
        $(location.hash + '.collapse').collapse('show');
    }
});

$(document).ready(function() {
    $(location.hash).on('shown.bs.collapse', function() {
        $('html, body').animate({
                scrollTop: $(location.hash).offset().top
            }, 500);
    });
});

});

