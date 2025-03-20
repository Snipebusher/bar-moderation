import pathlib
import urllib.parse

def buildPath(filename: str):
  pathItems = [pathlib.Path(filename)]
  while True:
    last = pathItems[-1]
    if last.parent == last:
      break
    pathItems.append(last.parent)
  return """<div id="path">
  <button onclick="openSelectPath()">GOTO</button>
%s
</div>""" % "\n".join("""
  <a href="/view/%s">%s</a>
""" % (str(item).strip("/"), item.name + ("/" if index else "") if item.name else str(item))
         for (index, item) in reversed(list(enumerate(pathItems))))

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
  --link-color: #007bff;
  --link-hover: #0056b3;
  --collapsible-bg: white;
  --filter-player-bg: white;
}

[data-theme="dark"] {
  --background-color: #121212;
  --text-color: white;
  --button-background: #007bff;
  --button-hover: #0056b3;
  --link-color: #1e90ff;
  --link-hover: #63b8ff;
  --collapsible-bg: #0f0f0f;
  --filter-player-bg: black;
}

body {
  background-color: var(--background-color);
  color: var(--text-color);
}
"""

STYLE = """
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
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
  color: var(--link-color);
  text-decoration: none;
  margin-right: 10px;
}
#path a:hover {
  text-decoration: underline;
  color: var(--link-hover);
}
a {
  color: var(--link-color);
}
a:hover {
  text-decoration: underline;
  color: var(--link-hover);
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
"""
