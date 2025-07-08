import pathlib
import urllib.parse
import os

def buildPath(filename: str):
  filenameToSend = filename.replace("\\", "//")
  pathItems = [pathlib.Path(filename)]
  while True:
    last = pathItems[-1]
    if last.parent == last:
      break
    pathItems.append(last.parent)

  if os.name != "posix":
    pathItems.append(pathlib.Path(str(pathItems[-1].drive)))

  path_links = "\n".join(
    """<a href="/view/{0}">{1}</a>""".format(
        str(item).replace("\\", "/").strip("/"),
        item.name or item.drive
    )
    for index, item in reversed(list(enumerate(pathItems)))
    if item.name or (item.drive and index == len(pathItems) - 1)
)

  choose_file = '<button onclick="openSelectPath()">Choose File</button>'
  start_replay = f'<button onclick="runReplay(\'{filenameToSend}\')" class="tooltip" data-tooltip="Run the current replay using the debug launcher" aria-label="Run the current replay using the debug launcher">Start Replay</button>' if os.name != "posix" and ".sdfz" in filename else ""

  settings_btn = """
  <button id="settingsButton" aria-label="Settings" style="background:none;border:none;cursor:pointer;padding:0;display:flex;align-items:center;justify-content:center;width:32px;height:32px;">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="var(--text-color)" style="width:100%;height:100%;">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  </button>
"""

  return f"""
<div id="path" style="display:flex;justify-content:space-between;align-items:center;padding:10px;background-color:rgba(0,0,0,0.1);border-bottom:1px solid rgba(0,0,0,0.2);">
  <div>
    {choose_file}
    {start_replay}
    {path_links}
  </div>
  {settings_btn}
</div>
"""

def buildPage(filename: str, content: str, *, style="", script=""):
    return """
<html>
  <head>
    <style>
{defaultStyle}
{theme_css}
    #settingsModal a {{ 
      background: none !important;
      padding: 0 !important;
      color: var(--link-color);
    }}
{givenStyle}
    </style>
    <script>
{defaultScript}

{givenScript}
    </script>
  </head>
  <body>
      {path}
    <div id="mainContent">
      {content}
    </div>
    <div id="settingsModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);justify-content:center;align-items:center;z-index:1500;">
      <div style="background-color:var(--background-color);color:var(--text-color);width:95%;max-width:1200px;max-height:95%;overflow-y:auto;padding:20px;border-radius:8px;position:relative;">
        <button id="settingsClose" aria-label="Close settings" style="position:absolute;top:12px;right:12px;background:none;border:none;cursor:pointer;font-size:16px;color:var(--text-color);">Close</button>
        <h2 style="margin-top:0;">Settings</h2>
        <div style="margin-top:10px;">
          <label for="themeSelector" style="display:block;margin-bottom:5px;">Theme:</label>
          <select id="themeSelector" style="width:100%;padding:8px;background-color:var(--background-color);color:var(--text-color);border:1px solid var(--text-color);border-radius:4px;">
            <option value="system">Device</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
        <hr style="margin:20px 0;border-color:var(--text-color);" />
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:0.9rem;flex-wrap:nowrap;">
          <div style="flex:1;text-align:left;">
            Developed by
            <a href="https://github.com/aurelienlt" target="_blank">aurelienlt</a>,
            <a href="https://github.com/Snipebusher" target="_blank">Snipebusher</a>
            and
            <a href="https://github.com/fritman1" target="_blank">fritman1</a>
          </div>
          <div style="flex:1;text-align:center;">
            <a href="https://github.com/Snipebusher/bar-moderation" target="_blank">
              <svg aria-hidden="true" height="32" viewBox="0 0 24 24" width="32">
                <path fill="var(--text-color)" d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.263.82-.582 0-.288-.01-1.05-.01-2.06-3.338.725-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.09-.745.083-.73.083-.73 1.205.084 1.84 1.237 1.84 1.237 1.07 1.835 2.807 1.305 3.492.998.108-.775.418-1.305.76-1.605-2.665-.305-5.466-1.332-5.466-5.93 0-1.31.468-2.38 1.236-3.22-.124-.303-.536-1.523.116-3.176 0 0 1.008-.322 3.3 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.29-1.552 3.296-1.23 3.296-1.23.655 1.653.243 2.873.12 3.176.77.84 1.235 1.91 1.235 3.22 0 4.61-2.804 5.625-5.476 5.92.43.37.81 1.102.81 2.222 0 1.606-.014 2.896-.014 3.286 0 .322.216.699.825.58A11.995 11.995 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
            </a>
          </div>
          <div style="flex:1;text-align:right;">
            v1.3
          </div>
        </div>
      </div>
    </div>
    <div class="context-menu" id="contextFilterMenu">
    <!-- Menu options will be inserted here dynamically -->
    </div>
  </body>
</html>
""".format(
    defaultStyle=STYLE,
    theme_css=THEME,
    givenStyle=style,
    defaultScript=SCRIPT,
    givenScript=script,
    path=buildPath(filename),
    content=content,
)

def buildErrorPage(filename: str, title: str, description: str):
    return buildPage(filename, "<h1>%s</h1><p>%s</p>" % (title, description))

THEME = """
[data-theme="light"] {
  --background-color: white;
  --text-color: black;
  --button-background: #007bff;
  --button-hover: #0056b3;
  --link-color: #1abc9c;
  --link-hover: #16a085;
  --collapsible-bg: white;
  --filter-player-bg: white;
  --draw-color: black;
}

[data-theme="dark"] {
  --background-color: #121212;
  --text-color: white;
  --button-background: #007bff;
  --button-hover: #0056b3;
  --link-color: #1abc9c;
  --link-hover: #48c9b0;
  --collapsible-bg: #0f0f0f;
  --filter-player-bg: black;
  --draw-color: white;
}
"""

STYLE = """
body {
  background-color: var(--background-color);
  color: var(--text-color);
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
}
.context-menu {
  position: absolute;
  background-color: #f9f9f9;
  border: 1px solid #ccc;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
  display: none;
  z-index: 1000;
}
.context-menu div {
  padding: 8px 16px;
  cursor: pointer;
}
.context-menu div:hover {
  background-color: #e0e0e0;
}
.tooltip-popup {
  position: absolute;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--text-color);
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 0.875rem;
  white-space: nowrap;
  pointer-events: none;
  z-index: 1000;
}
.collapsable {
  background-color: var(--collapsible-bg);
  color: var(--text-color);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px;
}
.collapsed .collapsable {
  display: none;
}
button {
  background-color: var(--button-background);
  color: white;
  padding: 10px 15px;
  font-size: 14px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
button:hover {
  background-color: var(--button-hover);
}
#themeSelector:hover {
  background-color: var(--button-hover);
}
#path {
  padding: 10px;
  background-color: rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(0, 0, 0, 0.2);
}
#path a {
  color: white;
  text-decoration: none;
  margin-left: 20px;
  margin-right: -20px;
}
#path a:hover {
  text-decoration: underline;
  background-color: var(--link-hover);
}
a {
  background-color: var(--link-color);
  color: white;
  padding: 5px 10px;
  border: none;
  border-radius: 5px;
  text-decoration: none;
  display: inline-block;
}
a:hover {
  text-decoration: none;
  background-color: var(--link-hover);
}
input, select, textarea {
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--text-color);
}
input::placeholder, textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}
input[type="checkbox"], input[type="radio"] {
  filter: invert(1);
}
[data-theme="light"] input[type="checkbox"], [data-theme="light"] input[type="radio"] {
  filter: invert(0);
}
"""
SCRIPT = """
function openSelectPath() {
  const path = prompt("GOTO path")
  if (!path) return
  window.location = "/view/" + path.replace(/^\\/+|\\/+$/g, "")
}
function runReplay(filename) {
  fetch('/runReplay', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename: filename }),
  })
  .then(response => response.json())
  .then(data => {
  if(data.status == "error") {
    alert(data.message)
  }
  else{
  console.log(data.message)}})
  .catch(error => console.error('Error:', error));
}
function toggleCollapsableVisibility(collapser) {
  const text = collapser.lastChild.textContent
  const prefix = text.substr(0, text.length-3)
  const suffix = text.substr(-3)
  if (suffix === "[-]") {
    collapser.textContent = prefix + "[+]"
  } else if (suffix === "[+]") {
    collapser.textContent = prefix + "[-]"
  }
  fixCollapsableVisibility(collapser)
}
function fixCollapsableVisibility(collapser) {
  const text = collapser.lastChild.textContent
  const suffix = text.substr(-3)
  if (suffix === "[+]") {
    collapser.parentElement.classList.add("collapsed")
  } else if (suffix === "[-]") {
    collapser.parentElement.classList.remove("collapsed")
  }
}
function isFilterCheckbox(checkbox) {
  return checkbox.type === "checkbox" && checkbox.value.startsWith("filter-")
}
function fixFilterCheckboxes(container) {
  const checkboxes = container.getElementsByTagName("input")
  const checked = {}
  const childrenChecked = {}
  for (let index = 0; index < checkboxes.length; index++) {
    const checkbox = checkboxes[index]
    if (!isFilterCheckbox(checkbox)) continue
    checked[checkbox.value.substr("filter-".length)] = checkbox.checked ? "selected" : "deselected"
    for (const cls of checkbox.classList) {
      if (cls.startsWith("parent-filter-")) {
        const filter = cls.substr("parent-filter-".length)
        if (!childrenChecked[filter]) childrenChecked[filter] = []
        childrenChecked[filter].push(checkbox.checked)
      }
    }
  }
  for (const filter in checked) {
    if (childrenChecked[filter]) {
      checked[filter] = childrenChecked[filter].every(x => x) ? "selected" :
                        childrenChecked[filter].every(x => !x) ? "deselected" :
                        "partially-selected"
    }
  }
  for (let index = 0; index < checkboxes.length; index++) {
    const checkbox = checkboxes[index]
    if (!isFilterCheckbox(checkbox)) continue
    checkbox.checked = checked[checkbox.value.substr("filter-".length)] === "selected"
  }
  for (const filter in checked) {
    for (const status of ["selected", "deselected", "partially-selected"]) {
      if (checked[filter] === status) {
        container.parentElement.classList.add(status + "-filter-" + filter)
      } else {
        container.parentElement.classList.remove(status + "-filter-" + filter)
      }
    }
  }
}

function updateContextMenu(playerId) {
  const contextMenu = document.getElementById('contextFilterMenu');
  console.log(contextMenu);
  contextMenu.innerHTML = ''; // Clear existing menu options
  console.log("hello there");
  let profileLink = "https://server4.beyondallreason.info/profile/" + playerId;
  let reportProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId;
  let actionProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#actions_tab";
  let detailProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#user_details_tab";
  //let reportsModLink =  "https://server4.beyondallreason.info/moderation/report?target_id="+playerId;
  //add menu option based on RealPLayerId recorded into the data field
  let menuOptions = [];
  menuOptions = [
        { text: 'Profile', action: function() { window.open(profileLink); } },
        { text: 'Reports', action: function() { window.open(reportProfileLink);}},
        { text: 'Actions', action: function() { window.open(actionProfileLink); } },
        { text: 'Details', action: function() { window.open(detailProfileLink); } }//,
        //{ text: 'mod reports', action: function() { window.open(reportsModLink); } }
    ];
  // Add menu options to the context menu
  menuOptions.forEach(option => {
      const menuItem = document.createElement('div');
      menuItem.textContent = option.text;
      menuItem.addEventListener('click', option.action);
      contextMenu.appendChild(menuItem);
  });
}

function updateFilterCheckboxes(container, updatedCheckbox) {
  if (!isFilterCheckbox(updatedCheckbox)) return
  const childClass = "parent-" + updatedCheckbox.value
  const checkboxes = container.getElementsByTagName("input")
  for (let index = 0; index < checkboxes.length; index++) {
    const checkbox = checkboxes[index]
    if (!isFilterCheckbox(checkbox)) continue
    if (checkbox.classList.contains(childClass)) {
      checkbox.checked = updatedCheckbox.checked
    }
  }
  fixFilterCheckboxes(container)
}
window.addEventListener("load", () => {
  const filterContainers = document.getElementsByClassName("filters")
  for (let index = 0; index < filterContainers.length; index++) {
    const filterContainer = filterContainers[index]
    fixFilterCheckboxes(filterContainer)
    const checkboxes = filterContainer.getElementsByTagName("input")
    for (let index = 0; index < checkboxes.length; index++) {
      const checkbox = checkboxes[index]
      if (!isFilterCheckbox(checkbox)) continue
      checkbox.addEventListener("change", () => updateFilterCheckboxes(filterContainer, checkbox))
    }
  }
})
document.addEventListener('DOMContentLoaded', function() {
  const hoverDelay = 500;
  const offsetX = 10;
  const offsetY = 20;

  document.querySelectorAll('.tooltip').forEach(el => {
    let timer = null;
    let tooltipEl = null;
    let shownOnce = false;
    let lastX = 0, lastY = 0;

    function clearTooltipAndTimer() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      if (tooltipEl) {
        tooltipEl.remove();
        tooltipEl = null;
      }
    }

    el.addEventListener('mouseenter', e => {
      shownOnce = false;
      clearTooltipAndTimer();
      lastX = e.pageX;
      lastY = e.pageY;
      timer = setTimeout(() => {
        const text = el.getAttribute('data-tooltip');
        if (!text) return;
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'tooltip-popup';
        tooltipEl.textContent = text;
        document.body.appendChild(tooltipEl);
        tooltipEl.style.left = (lastX + offsetX) + 'px';
        tooltipEl.style.top  = (lastY + offsetY) + 'px';
        shownOnce = true;
        timer = null;
      }, hoverDelay);
    });

    el.addEventListener('mousemove', e => {
      lastX = e.pageX;
      lastY = e.pageY;
      if (!shownOnce) {
        if (timer) {
          clearTimeout(timer);
        }
        timer = setTimeout(() => {
          const text = el.getAttribute('data-tooltip');
          if (!text) return;
          tooltipEl = document.createElement('div');
          tooltipEl.className = 'tooltip-popup';
          tooltipEl.textContent = text;
          document.body.appendChild(tooltipEl);
          tooltipEl.style.left = (lastX + offsetX) + 'px';
          tooltipEl.style.top  = (lastY + offsetY) + 'px';
          shownOnce = true;
          timer = null;
        }, hoverDelay);
      } else {
        if (tooltipEl) {
          tooltipEl.remove();
          tooltipEl = null;
        }
        if (timer) {
          clearTimeout(timer);
          timer = null;
        }
      }
    });

    el.addEventListener('mouseleave', e => {
      clearTooltipAndTimer();
      shownOnce = false;
    });
  });
const labels = document.querySelectorAll('label');
const contextMenu = document.getElementById('contextFilterMenu');
let currentLabel = null;
labels.forEach(label => {
    label.addEventListener('contextmenu', function(e) {
    //we reject if no player- in class name
    if (!Array.from(label.classList).some(className => className.startsWith('player-'))) {
      return; // Skip showing the context menu for this label
    }
    e.preventDefault();
    currentLabel = label;
    const playerId = label.dataset.id;
    updateContextMenu(playerId);
    contextMenu.style.display = 'block';
    contextMenu.style.left = e.pageX + 'px';
    contextMenu.style.top = e.pageY + 'px';
    });
  });
  document.addEventListener('click', function() {
    contextMenu.style.display = 'none';
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const themeSelector = document.getElementById("themeSelector");
  const savedTheme = localStorage.getItem("theme") || "system";
  applyTheme(savedTheme);
  if (themeSelector) {
    themeSelector.value = savedTheme;
    themeSelector.addEventListener("change", function () {
      const selectedTheme = themeSelector.value;
      applyTheme(selectedTheme);
      localStorage.setItem("theme", selectedTheme);
    });
  }
  function applyTheme(theme) {
    if (theme === "system") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute("data-theme", prefersDark ? "dark" : "light");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
  }
  const settingsButton = document.getElementById("settingsButton");
  const settingsModal = document.getElementById("settingsModal");
  const settingsClose = document.getElementById("settingsClose");
  if (settingsButton && settingsModal) {
    settingsButton.addEventListener("click", () => {
      settingsModal.style.display = "flex";
      document.body.classList.add("modal-open");
      if (themeSelector) {
        themeSelector.value = localStorage.getItem("theme") || "system";
      }
    });
  }
  if (settingsClose && settingsModal) {
    settingsClose.addEventListener("click", () => {
      settingsModal.style.display = "none";
      document.body.classList.remove("modal-open");
    });
  }
  if (settingsModal) {
    settingsModal.addEventListener("click", (e) => {
      if (e.target === settingsModal) {
        settingsModal.style.display = "none";
        document.body.classList.remove("modal-open");
      }
    });
  }
  const collapsers = document.getElementsByClassName("collapser");
  for (let index = 0; index < collapsers.length; index++) {
    fixCollapsableVisibility(collapsers[index]);
    collapsers[index].addEventListener("click", event => toggleCollapsableVisibility(event.target));
  }
  const filterContainers = document.getElementsByClassName("filters");
  for (let index = 0; index < filterContainers.length; index++) {
    const filterContainer = filterContainers[index];
    fixFilterCheckboxes(filterContainer);
    const checkboxes = filterContainer.getElementsByTagName("input");
    for (let idx = 0; idx < checkboxes.length; idx++) {
      const checkbox = checkboxes[idx];
      if (!isFilterCheckbox(checkbox)) continue;
      checkbox.addEventListener("change", () => updateFilterCheckboxes(filterContainer, checkbox));
    }
  }
});
// Shared setting templates for reuse
const settingTheme = `
  <div class="setting-group">
    <label for="themeSelector">Theme:</label>
    <select id="themeSelector">
      <option value="system">Device</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </div>
`;

const settingBackgroundEffect = `
  <div class="setting-group">
    <label for="backgroundEffect">Settings Background:</label>
    <select id="backgroundEffect">
      <option value="none">None</option>
      <option value="darken" selected>Darken</option>
      <option value="blur">Blur</option>
      <option value="both">Both</option>
    </select>
  </div>
`;

const basicContainer = document.getElementById("settingsBasic");
const advancedContainer = document.getElementById("settingsAdvanced");


// Order Setup
if (basicContainer && advancedContainer) {
  basicContainer.innerHTML = settingTheme;
  advancedContainer.innerHTML = settingTheme + settingBackgroundEffect;
}


let originalValues = {
  theme: localStorage.getItem("theme") || "system",
  backgroundEffect: localStorage.getItem("backgroundEffect") || "darken"
};

function getCurrentValues() {
  return {
    theme: document.getElementById("themeSelector")?.value,
    backgroundEffect: document.getElementById("backgroundEffect")?.value
  };
}

function valuesChanged() {
  const current = getCurrentValues();
  return current.theme !== originalValues.theme || current.backgroundEffect !== originalValues.backgroundEffect;
}

function activateTab(tab) {
  const basic = document.getElementById("settingsBasic");
  const advanced = document.getElementById("settingsAdvanced");
  const btnBasic = document.getElementById("tabBasic");
  const btnAdvanced = document.getElementById("tabAdvanced");

  if (tab === "basic") {
    btnBasic.classList.add("active");
    btnAdvanced.classList.remove("active");
    basic.style.display = "block";
    advanced.style.display = "none";
  } else {
    btnBasic.classList.remove("active");
    btnAdvanced.classList.add("active");
    basic.style.display = "none";
    advanced.style.display = "block";
  }
}

document.getElementById("tabBasic").addEventListener("click", () => activateTab("basic"));
document.getElementById("tabAdvanced").addEventListener("click", () => activateTab("advanced"));

let previewActive = false;
const previewBtn = document.getElementById("settingsPreview");
const modal = document.getElementById("settingsModal");
const modalContent = modal?.querySelector(".modal-content") || modal?.children[0];

if (previewBtn && modalContent) {
  previewBtn.addEventListener("click", () => {
    previewActive = !previewActive;
    if (previewActive) {
      modalContent.style.display = "none";
      modal.style.background = "transparent";
      modal.style.backdropFilter = "none";
    } else {
      modalContent.style.display = "block";
      applyModalBackground();
    }
  });
}

function applyModalBackground() {
  const bg = localStorage.getItem("backgroundEffect") || "darken";
  switch (bg) {
    case "none":
      modal.style.background = "transparent";
      modal.style.backdropFilter = "none";
      break;
    case "darken":
      modal.style.background = "rgba(0,0,0,0.5)";
      modal.style.backdropFilter = "none";
      break;
    case "blur":
      modal.style.background = "transparent";
      modal.style.backdropFilter = "blur(10px)";
      break;
    case "both":
      modal.style.background = "rgba(0,0,0,0.5)";
      modal.style.backdropFilter = "blur(10px)";
      break;
  }
}

document.getElementById("settingsSave").addEventListener("click", () => {
  const themeSelector = document.getElementById("themeSelector");
  const bgSelector = document.getElementById("backgroundEffect");
  if (themeSelector) localStorage.setItem("theme", themeSelector.value);
  if (bgSelector) localStorage.setItem("backgroundEffect", bgSelector.value);
  originalValues = getCurrentValues();
  modalContent.style.display = "block";
  previewActive = false;
  modal.style.display = "none";
  document.body.classList.remove("modal-open");
  applyTheme(themeSelector.value);
  applyModalBackground();
});

document.getElementById("settingsDefault").addEventListener("click", () => {
  localStorage.clear();
  document.getElementById("themeSelector").value = "system";
  document.getElementById("backgroundEffect").value = "darken";
  applyTheme("system");
  applyModalBackground();
});

function promptCancel() {
  if (valuesChanged()) {
    if (confirm("You have unsaved changes. Discard them?")) {
      modalContent.style.display = "block";
      previewActive = false;
      modal.style.display = "none";
      document.body.classList.remove("modal-open");
      document.getElementById("themeSelector").value = originalValues.theme;
      document.getElementById("backgroundEffect").value = originalValues.backgroundEffect;
      applyTheme(originalValues.theme);
      applyModalBackground();
    }
  } else {
    modalContent.style.display = "block";
    previewActive = false;
    modal.style.display = "none";
    document.body.classList.remove("modal-open");
  }
}

document.getElementById("settingsCancel").addEventListener("click", promptCancel);
modal.addEventListener("click", (e) => {
  if (e.target === modal) promptCancel();
});

document.addEventListener("DOMContentLoaded", function () {
  const themeSelector = document.getElementById("themeSelector");
  const bgSelector = document.getElementById("backgroundEffect");

  if (themeSelector) {
    themeSelector.value = originalValues.theme;
    themeSelector.addEventListener("change", () => {
      applyTheme(themeSelector.value);
    });
  }

  if (bgSelector) {
    bgSelector.value = originalValues.backgroundEffect;
    bgSelector.addEventListener("change", () => {
      applyModalBackground();
    });
  }

  applyTheme(originalValues.theme);
  applyModalBackground();
});

function applyTheme(theme) {
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.setAttribute("data-theme", prefersDark ? "dark" : "light");
  } else {
    document.documentElement.setAttribute("data-theme", theme);
  }
}
"""
