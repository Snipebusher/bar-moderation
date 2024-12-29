import pathlib
import urllib.parse

def buildPath(filename: str):
  pathItems = [pathlib.Path(filename)]
  while True:
    last = pathItems[-1]
    if last.parent == last: break
    pathItems.append(last.parent)

  return """<div id="path">
  <button onclick="openSelectPath()">GOTO</button>
%s
</div>""" % "\n".join("""
  <a href="/view/%s">%s</a>
""" % (
      str(item).strip("/"),
      item.name.removesuffix("/") + ("/" if index else "")
    ) for (index, item) in reversed(list(enumerate(pathItems))))

def buildPage(filename: str, content: str, *, style="", script=""):
  return """
<html>
  <head>
    <style>
{defaultStyle}

{givenStyle}
    </style>
    <script>
{defaultScript}

{givenScript}
    </script>
  </head>
  <body>
{path}

{content}
  </body>
</html>
""".format(
    defaultStyle=STYLE, givenStyle=style,
    defaultScript=SCRIPT, givenScript=script,
    path=buildPath(filename), content=content)

def buildErrorPage(filename: str, title: str, description: str):
  return buildPage(filename, """
<h1>%s</h1>
<p>%s</p>
""" % (title, description))

STYLE = """
.collapsed .collapsable {
  display: none !important;
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

window.addEventListener("load", () => {
  const collapsers = document.getElementsByClassName("collapser")
  for (let index = 0; index < collapsers.length; index++) {
    fixCollapsableVisibility(collapsers[index])
    collapsers[index].addEventListener("click", event => toggleCollapsableVisibility(event.target))
  }
})

function isFilterCheckbox(checkbox) {
  return checkbox.type === "checkbox" && checkbox.value.startsWith("filter-")
}

function fixFilterCheckboxes(container) {
  const checkboxes = container.getElementsByTagName("input")
  const checked = {}
  const childrenChecked = {}
  // list the checkbox and read if checked or not
  for (let index = 0; index < checkboxes.length; index++) {
    const checkbox = checkboxes[index]
    if (!isFilterCheckbox(checkbox)) continue
    checked[checkbox.value.substr("filter-".length)] =
      checkbox.checked ? "selected" : "deselected"
    for (const cls of checkbox.classList) {
      if (cls.startsWith("parent-filter-")) {
        const filter = cls.substr("parent-filter-".length)
        if (!childrenChecked[filter]) childrenChecked[filter] = []
        childrenChecked[filter].push(checkbox.checked)
      }
    }
  }
  // apply children status to parent status
  for (const filter in checked) {
    if (childrenChecked[filter]) {
      checked[filter] = childrenChecked[filter].every(x => x) ? "selected" :
                        childrenChecked[filter].every(x => !x) ? "deselected" :
                        "partially-selected"
    }
  }
  // fix the checked state of all the checkboxes
  for (let index = 0; index < checkboxes.length; index++) {
    const checkbox = checkboxes[index]
    if (!isFilterCheckbox(checkbox)) continue
    checkbox.checked = checked[checkbox.value.substr("filter-".length)] === "selected"
  }
  // apply all the classes to the parent
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
