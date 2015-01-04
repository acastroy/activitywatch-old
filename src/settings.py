import json
import os

_instance = None


class Singleton:
    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.cls(*args, **kwds)
        return self.instance


@Singleton
class Settings(dict):
    def __init__(self):
        # TODO: If settingsfile doesn't exist, create one from default settings file
        # TODO: Store in users application data folder
        dict.__init__(self)
        filepath = os.path.realpath(__file__)
        srcpath = os.path.dirname(filepath)
        rootpath = os.path.dirname(srcpath)
        with open(rootpath + "/settings.json") as f:
            self.update(json.loads(f.read()))

        print("Loaded settings:")
        print("  Location: {}".format(self["location"]))
        print("  Tags: {}".format(self["tags"]))
        print("")


class SettingsException(Exception):
    pass


assert Settings() is Settings()
