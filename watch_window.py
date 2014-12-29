#!/usr/bin/python3

#####################
#  Stdlib Packages  #
#####################

import os
import sys
import subprocess
import unittest
import logging

import time
from time import sleep

from datetime import datetime

#####################
# External packages #
#####################

import psutil

import Xlib
import Xlib.display
from Xlib import X, Xatom

display = Xlib.display.Display()
screen = display.screen()

def main():
    current_window = None
    selected_at = datetime.now()
    while True:
        sleep(1.0)

        window = display.get_input_focus().focus
        pid = get_window_pid(window)
        name, cls = get_window_name(window)

        if not current_window:
            print("First focus is '{}' with PID: {}".format(cls[1], pid))
            current_window = window
            selected_at = datetime.now()
            continue
        
        if current_window.id == window.id:
            # Skip if same as before
            if current_window.id == window.id:
                continue

        # New window has been focused
        # Add actions such as log to local db here
        print("Window selected for: {}\n".format(datetime.now() - selected_at))
        
        print("Switched to '{}' with PID: {}".format(cls[1], pid))
        current_window = window
        selected_at = datetime.now()

        proc = process_by_pid(pid)
        print("\t{}".format(proc.cmdline()))

def get_window_name(window):
    name = None
    while window:
        cls = window.get_wm_class()
        name = window.get_wm_name()
        if not cls:
            window = window.query_tree().parent
        else:
            break
    return name, cls

def get_window_pid(window):
    pid_property = window.get_full_property(display.get_atom("_NET_WM_PID"), X.AnyPropertyType)
    pid = pid_property.value[-1]
    return pid


def get_window(window_id):
    return display.create_resource_object('window', window_id)

def process_by_pid(pid):
    p = psutil.Process(int(pid))
    logging.debug("Got process: " + str(p.cmdline()))
    return p


class Tests(unittest.TestCase):
    def test_self(self):
        process = process_by_pid(os.getpid())
        print(process)

    def test_xlib(self):
        pass
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        del sys.argv[1]
        if cmd == "test":
            unittest.main()
        elif cmd == "":
            pass
        else:
            print("Unknown command '{}'".format(cmd))
    else:
        main()
