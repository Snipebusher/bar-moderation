import http.server
import pathlib
import urllib.parse
import os
import traceback
import json
from .directories import buildDirectoryPage
from .summaries import buildReplayPage
from .pages import buildErrorPage

defaultPath = str(pathlib.Path(os.getcwd()).absolute())

class RequestHandler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    self.handle_one_request
    self.path = self.path.replace("%22", "") # Credit to fritman1
    url = urllib.parse.urlparse(self.path)
    path = url.path.strip("/") + "/"
    if path.startswith("view/"):
      filepath = pathlib.Path(urllib.parse.unquote(path).removeprefix("view").strip("/"))
      if not filepath.drive:
        filepath = pathlib.Path("/" + str(filepath)).absolute()
      elif not filepath.is_absolute():
        filepath = pathlib.Path(filepath.drive + "/")
      if filepath.is_dir():
        self.send_response(200, "OK")
        self.send_header('Content', 'text/html; charset=UTF-8')
        self.end_headers()
        self.wfile.write(buildDirectoryPage(str(filepath)).encode())
      elif filepath.is_file():
        try:
          page = buildReplayPage(str(filepath))
        except Exception as e:
          traceback.print_exception(e)
          self.send_response(400, "Not a replay")
          self.end_headers()
          self.wfile.write(buildErrorPage(str(filepath), "Failed to parse replay file", "see server logs for full error trace").encode())
        else:
          self.send_response(200, "OK")
          self.send_header('Content', 'text/html; charset=UTF-8')
          self.end_headers()
          self.wfile.write(page.encode())
      else:
        self.send_response(404, "Not Found")
        self.end_headers()
        self.wfile.write(buildErrorPage(str(filepath), "Not found", "The file or directory was not found").encode())
    else:
      self.send_response(307, "Temporary Redirect")
      self.send_header('Location', "/view/%s" % (defaultPath.removeprefix("/")))
      self.end_headers()


  def do_POST(self):
    self.path = self.path.replace("%22", "") # Credit to fritman1
    url = urllib.parse.urlparse(self.path)
    path = url.path.strip("/") + "/"
    if path.startswith("runReplay/"):
      content_length = int(self.headers['Content-Length'])
      post_data = self.rfile.read(content_length)
      try:
        # Decode the data and parse it as JSON
        json_data = json.loads(post_data.decode('utf-8'))
        filename = json_data.get('filename')  # Access the filename from the JSON object
        # Print the received message
        print("Run replay :", filename)
      except json.JSONDecodeError as e:
        print("Error decoding JSON !:", e)
      goodfilename = filename.replace("//", "\\")
      if ".sdfz" in goodfilename:
        try:
          os.startfile(goodfilename)
        except Exception:
          print("Error starting replay, make sure you have the debug launcher installed and set as default application for openning replay files (.sfbz)")