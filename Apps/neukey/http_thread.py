from http.server import HTTPServer
from os import curdir, sep

import threading

class httpServerThread() :
    def __init__(self, port, handler) :
        self.port = port
        self.handler = handler
        self.server = None
        self.thread = None

    def start(self) :
        self.server = HTTPServer(('', self.port), self.handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def stop(self) :
        self.server.shutdown()
        self.thread.join()