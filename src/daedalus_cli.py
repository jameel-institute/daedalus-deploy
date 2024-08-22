"""
Usage:
  ./daedalus start [--pull] [<configname>]
  ./daedalus stop  [--volumes] [--network] [--kill] [--force]
  ./daedalus destroy
  ./daedalus status
  ./daedalus upgrade

Options:
  --pull              Pull images before starting
  --volumes           Remove volumes (WARNING: irreversible data loss)
  --network           Remove network
  --kill              Kill the containers (faster, but possible db corruption)
"""

import docopt
import os
import os.path
import pickle
import time
import timeago

from src.daedalus_config import DaedalusConfig
from src.daedalus_constellation import DaedalusConstellation


def parse(argv=None):
    path = "config"
    config_name = None
    dat = docopt.docopt(__doc__, argv)
    if dat["start"]:
        action = "start"
        config_name = dat["<configname>"]
        args = {"pull_images": dat["--pull"]}
        options = {}
    elif dat["stop"]:
        action = "stop"
        args = {"kill": dat["--kill"],
                "remove_network": dat["--network"],
                "remove_volumes": dat["--volumes"]}
        options = {}
    elif dat["destroy"]:
        action = "stop"
        args = {"kill": True,
                "remove_network": True,
                "remove_volumes": True}
        options = {}
    elif dat["status"]:
        action = "status"
        args = {}
        options = {}
    elif dat["upgrade"]:
        args = {}
        options = {}
        action = "upgrade"
    return path, config_name, action, args, options


def path_last_deploy(path):
    return path + "/.last_deploy"


def save_config(path, config_name, cfg):
    dat = {"config_name": config_name,
           "time": time.time(),
           "data": cfg}
    with open(path_last_deploy(path), "wb") as f:
        pickle.dump(dat, f)


def read_config(path):
    with open(path_last_deploy(path), "rb") as f:
        dat = pickle.load(f)
    return dat


def load_config(path, config_name=None, options=None):
    if os.path.exists(path_last_deploy(path)):
        dat = read_config(path)
        when = timeago.format(dat["time"])
        cfg = DaedalusConfig(path, dat["config_name"], options=options)
        config_name = dat["config_name"]
        print("[Loaded configuration '{}' ({})]".format(
            config_name or "<base>", when))
    else:
        if (config_name is None):
            raise Exception(
             "Config name must be provided when there is no " +
             "previous deploy config,")
        cfg = DaedalusConfig(path, config_name, options=options)
    return config_name, cfg


def remove_config(path):
    p = path_last_deploy(path)
    if os.path.exists(p):
        print("Removing configuration")
        os.unlink(p)


def main(argv=None):
    path, config_name, action, args, options = parse(argv)
    config_name, cfg = load_config(path, config_name, options)
    use_vault = action == "start"
    constellation = DaedalusConstellation(cfg, use_vault)

    if args.get("remove_volumes"):
        print("WARNING! THIS WILL REMOVE ALL VOLUMES CAUSING " +
              "IRREVERSIBLE DATA LOSS!")
        if input("Do you want to continue? [yes/no] ") != "yes":
            print("Not continuing")
            return

    if action == "upgrade":
        constellation.obj.restart(pull_images=True)
    elif action == "start":
        save_config(path, config_name, cfg)
        constellation.start(args)
    else:
        constellation.obj.__getattribute__(action)(**args)
        if action == "stop" and args["remove_volumes"]:
            remove_config(path)
