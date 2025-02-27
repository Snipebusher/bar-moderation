import webbrowser
import pathlib
import argparse
import http.server
import threading
import time
import signal
from lib import server
import tkinter as tk
from tkinter import filedialog
import os
import subprocess

from lib.pages import handle_new_instance

class CustomRequestHandler(server.RequestHandler):
    def do_GET(self):
        if self.path == "/new_instance":
            subprocess.Popen(["python", "main.py"])
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"New instance started")
            # IMPORTANT: Return here so we don't call super().do_GET()
            return
        else:
            super().do_GET()

def run_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("SDFZ files", "*.sdfz")])
    root.destroy()
    return file_path

parser = argparse.ArgumentParser(
  prog="BARreplays",
  description="Runs a HTTP server to quickly see local BAR replays")

parser.add_argument("-o", "--open",
                    action="store_true",
                    help="open in browser")
parser.add_argument("DIR", nargs='?',
                    default=server.defaultPath,
                    help="default local directory or replay file to open")
parser.add_argument("-p", "--port", 
                    type=int, default=8888,
                    help="port to listen to")
parser.add_argument("-b", "--bind",
                    default="localhost",
                    help="hostname to listen to")

if __name__ == "__main__":
  args = parser.parse_args()
  server_address = (args.bind, args.port)
  if args.DIR:
    server.defaultPath = str(pathlib.Path(args.DIR).absolute())
  
  selected_file = run_file_dialog()
  if selected_file:
    server.defaultPath = selected_file
  
  webbrowser.register('opera', None, webbrowser.BackgroundBrowser("S:\\Apps\\Opera GX\\Opera GX\\opera.exe"))
  webbrowser.get('opera').open("http://localhost:8888")

  httpd = http.server.HTTPServer(server_address, server.RequestHandler)
  thread = threading.Thread(target=httpd.serve_forever, daemon=True)
  thread.start()
  time.sleep(0.5)
  if thread.is_alive():
    print("listening to", "http://%s:%s/" % server_address)
    if args.open:
      webbrowser.open_new_tab("http://%s:%s/" % server_address)
    signal.signal(signal.SIGINT, lambda sig, frame: httpd.shutdown())
  thread.join()
