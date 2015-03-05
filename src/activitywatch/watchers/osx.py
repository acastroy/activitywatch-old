import logging

from AppKit import NSWorkspace

from ..base import Watcher

class OSXWatcher(Watcher):
    NAME = "osx"

    def run(self):
        logging.warning("OS X Watcher not implemented")
        return

