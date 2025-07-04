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
  htmltop = ""
  if os.name != "posix" and ".sdfz" in filename:
    htmltop ="""<div id="path">
      <button onclick="openSelectPath()">Choose File</button>
      <button onclick="runReplay('{}')" class="tooltip" data-tooltip="Run the current replay using the debug launcher" aria-label="Run the current replay using the debug launcher">Start Replay</button>
  {}
  </div>""".format(filenameToSend, "\n".join(
      """<a href="/view/{}">{}{}</a>""".format(
          str(item).strip("/"),
          item.name,
          "/" if index else "" if item.name else str(item))
        for (index, item) in reversed(list(enumerate(pathItems)))))
  else:
    htmltop ="""<div id="path">
      <button onclick="openSelectPath()">Choose File</button>
  {}
  </div>""".format("\n".join(
      """<a href="/view/{}">{}{}</a>""".format(
          str(item).strip("/"),
          item.name,
          "/" if index else "" if item.name else str(item))
        for (index, item) in reversed(list(enumerate(pathItems)))))
  return htmltop



def buildPage(filename: str, content: str, *, style="", script=""):
    return """
<html>
  <head>
    <style>
{defaultStyle}
{theme_css}
{givenStyle}
    </style>
    <script>
{defaultScript}

{givenScript}

document.addEventListener("DOMContentLoaded", function () {{
  const themeSelector = document.getElementById("themeSelector");
  const savedTheme = localStorage.getItem("theme") || "system";
  themeSelector.value = savedTheme;
  applyTheme(savedTheme);
  themeSelector.addEventListener("change", function () {{
    const selectedTheme = themeSelector.value;
    applyTheme(selectedTheme);
    localStorage.setItem("theme", selectedTheme);
  }});
  function applyTheme(theme) {{
    if (theme === "system") {{
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute("data-theme", prefersDark ? "dark" : "light");
    }} else {{
      document.documentElement.setAttribute("data-theme", theme);
    }}
  }}
  const collapsers = document.getElementsByClassName("collapser");
  for (let index = 0; index < collapsers.length; index++) {{
    fixCollapsableVisibility(collapsers[index]);
    collapsers[index].addEventListener("click", event => toggleCollapsableVisibility(event.target));
  }}
  const filterContainers = document.getElementsByClassName("filters");
  for (let index = 0; index < filterContainers.length; index++) {{
    const filterContainer = filterContainers[index];
    fixFilterCheckboxes(filterContainer);
    const checkboxes = filterContainer.getElementsByTagName("input");
    for (let index = 0; index < checkboxes.length; index++) {{
      const checkbox = checkboxes[index];
      if (!isFilterCheckbox(checkbox)) continue;
      checkbox.addEventListener("change", () => updateFilterCheckboxes(filterContainer, checkbox));
    }}
  }}
}});
    </script>
  </head>
  <body>
{path}
{content}
  
  <div class="context-menu" id="contextFilterMenu">
    <!-- Menu options will be inserted here dynamically -->
  </div>
  
  </body>
  <select id="themeSelector">
    <option value="system">Device</option>
    <option value="light">Light</option>
    <option value="dark">Dark</option>
  </select>
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
#themeSelector {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: var(--button-background);
  color: white;
  padding: 10px 20px;
  font-size: 14px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
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
  let profileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId;
  let reportProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId;
  let actionProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#actions_tab";
  let detailProfileLink = "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#user_details_tab";
  let reportsModLink =  "https://server4.beyondallreason.info/moderation/report?target_id="+playerId;

  // Define menu options based on the span text
  let menuOptions = [];
  menuOptions = [
        { text: 'profile', action: function() { window.open(profileLink); } },
        { text: 'reports', action: function() { window.open(reportProfileLink);}},
        { text: 'actions', action: function() { window.open(actionProfileLink); } },
        { text: 'details', action: function() { window.open(detailProfileLink); } },
        { text: 'mod reports', action: function() { window.open(reportsModLink); } }
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
      // Reset for new hover-enter
      shownOnce = false;
      clearTooltipAndTimer();
      lastX = e.pageX;
      lastY = e.pageY;
      // Start timer to show
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
    // Check if the label's class contains "player"
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
"""
