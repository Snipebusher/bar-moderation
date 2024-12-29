import http.server
import pathlib
import urllib.parse
import os
import traceback
from .directories import buildDirectoryPage
from .summaries import buildReplayPage
from .pages import buildErrorPage

defaultPath = str(pathlib.Path(os.getcwd()).absolute())

class RequestHandler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    self.handle_one_request
    url = urllib.parse.urlparse(self.path)
    path: str = url.path.strip("/") + "/"
    if path.startswith("view/"):
      filepath = pathlib.Path(urllib.parse.unquote(path).removeprefix("view").removesuffix("/") or "/").absolute()
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
