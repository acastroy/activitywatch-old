from abc import abstractmethod, ABCMeta, abstractproperty
import json
import logging

import threading
from datetime import datetime, timedelta

import pyzenobase
from .settings import Settings, SettingsException


class Activity(dict):                                                                    
    def __init__(self, tags: str or "list[str]", started_at, ended_at, **kwargs):
        dict.__init__(self)
        self["tags"] = tags
        if "cmd" in kwargs:
            # TODO: Keep?
            cmd = kwargs.pop("cmd")
            cmd = list(filter(lambda s: s[0] != "-", cmd))
            self["cmd"] = cmd
        self["start"] = started_at
        self["end"] = ended_at

        self.update(kwargs)

        msg = ""
        msg += "Logged activity '{}':".format(tags)
        msg += "  Started: {}".format(self["start"])
        msg += "  Ended: {}".format(self["end"])
        msg += "  Duration: {}".format(self.duration())
        if "cmd" in self:
            msg += "  Command: {}".format(self["cmd"])
        logging.debug(msg)

    def duration(self) -> timedelta:
        return self["end"] - self["start"]

    def to_zenobase_event(self) -> pyzenobase.ZenobaseEvent:
        # TODO: Add misc fields into note field
        data = {"tag": self["tags"],
                "timestamp": self["start"],
                "duration": self.duration().total_seconds()*1000}
        return pyzenobase.ZenobaseEvent(data)

    def to_json_dict(self) -> dict:
        data = self.copy()
        data["start"] = data["start"].isoformat()
        data["end"] = data["end"].isoformat()
        return data

    def to_json_str(self) -> str:
        data = self.to_json_dict()
        return json.dumps(data)


class Agent(threading.Thread):
    """Base class for Watchers, Filters and Watchers"""

    def __init__(self):
        # TODO: This will cause problems with Filters which will run both Watcher.__init__ and Logger.__init__
        threading.Thread.__init__(self, name=self.__class__.__name__)

    @abstractmethod
    def run(self):
        pass

    @property
    def identifier(self):
        """Identifier for agent, used in settings and as a module name shorter than the class name"""
        return self.name[0:-len(self.agent_type)].lower()

    @property
    def settings(self):
        """Returns the settings for the current module from the global settings"""
        if not self.identifier:
            raise Exception("identifier was not set, could not get settings")
        settings = Settings()
        if self.agent_type+"s" not in settings:
            raise SettingsException("settings file appears to be corrupt, root-level key {} not found"
                                    .format(self.agent_type + "s"))
        if self.identifier in settings[self.agent_type+"s"]:
            return settings[self.agent_type+"s"][self.identifier]
        else:
            settings[self.agent_type][self.identifier] = self.default_settings
            logging.warning("Settings for agent '{}' missing, creating entry with defaults")

    @property
    def agent_type(self) -> str:
        if isinstance(self, Logger):
            return "logger"
        elif isinstance(self, Filter):
            return "filter"
        elif isinstance(self, Watcher):
            return "watcher"
        else:
            raise Exception("Unknown agent type")

    @abstractmethod
    def add_activity(self, activity: "Activity"):
        pass

    def add_activities(self, activities: "Activity"):
        for activity in activities:
            self.add_activity(activity)

    @property
    def default_settings(self):
        """Default settings for agent, will be inserted into settingsfile if entry is missing. Override to change."""
        return {}


class Logger(Agent):
    """
    Base class for loggers

    Listens to watchers and/or filters and logs activities with a
    method that should be defined by the subclass.
    """

    def __init__(self):
        Agent.__init__(self)
        self.watchers = set()

        # Must be thread-safe
        self._activities = []
        self._activities_lock = threading.Lock()

    # Only here to keep editor from complaining about unimplemented method
    @abstractmethod
    def run(self):
        pass

    def add_activity(self, activity: Activity):
        if not isinstance(activity, Activity):
            raise TypeError("{} is not an Activity".format(activity))
        with self._activities_lock:
            self._activities.append(activity)

    def flush_activities(self) -> "list[Activity]":
        with self._activities_lock:
            activities = self._activities
            self._activities = []
        return activities

    def add_watcher(self, watcher: "Watcher"):
        """Start listening to watchers here"""
        if not isinstance(watcher, Watcher):
            raise TypeError("{} is not a Watcher".format(watcher))

        self.watchers.add(watcher)
        if self not in watcher.loggers:
            watcher.add_logger(self)

    def add_watchers(self, watchers: "list[Watcher]"):
        for watcher in watchers:
            self.add_watcher(watcher)


class Watcher(Agent):
    """
    Base class for watchers

    Watches for activities with a method that should be defined by the
    subclass and forwards those activities to connected loggers and/or
    filters.
    """

    def __init__(self):
        Agent.__init__(self)
        self.loggers = set()

    # Only here to keep editor from complaining about unimplemented method
    @abstractmethod
    def run(self):
        pass

    def add_logger(self, logger: Logger):
        """Should only be called from Logger.add_watcher"""
        if not isinstance(logger, Logger):
            raise TypeError("{} was not a Logger".format(logger))

        self.loggers.add(logger)
        if self not in logger.watchers:
            logger.add_watcher(logger)

    def add_loggers(self, loggers: "list[Logger]"):
        for logger in loggers:
            self.add_logger(logger)

    def add_activity(self, activity: Activity):
        for logger in self.loggers:
            logger.add_activity(activity)


class Filter(Logger, Watcher):
    """
    Base class for filters

    Acts as both a logger and a watcher, effectively being able to do
    certain operations on the received activities before sending them
    forward in the chain.
    """

    def __init__(self):
        Logger.__init__(self)
        Watcher.__init__(self)

    # Only here to keep editor from complaining about unimplemented method
    @abstractmethod
    def run(self):
        pass
