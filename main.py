#!/usr/bin/env python3

import pathlib
import argparse
import http.server
import webbrowser
import threading
import time
import signal
from lib import server

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
  httpd = http.server.HTTPServer(server_address, server.RequestHandler)
  thread = threading.Thread(target=httpd.serve_forever, daemon=True)
  thread.start()
  time.sleep(0.5)
  if thread.is_alive():
    print("listening to", "http://%s:%s/" % server_address)
    if args.open:
      webbrowser.open_new_tab("http://%s:%s/")
    signal.signal(signal.SIGINT, lambda sig, frame: httpd.shutdown())
  thread.join()
