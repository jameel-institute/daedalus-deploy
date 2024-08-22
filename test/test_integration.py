import json
import requests
import os
from urllib3.exceptions import InsecureRequestWarning

import constellation.docker_util as docker_util

from src import daedalus_config
from src import daedalus_constellation


def test_start_daedalus():
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    # use a config that doesn't involve vault secrets
    cfg = daedalus_config.DaedalusConfig("config", "fakeproxy")
    constellation = daedalus_constellation.DaedalusConstellation(cfg, False)
    constellation.start({})
    constellation.obj.status()

    assert docker_util.network_exists("daedalus")
    assert docker_util.volume_exists("daedalus-data")
    assert docker_util.volume_exists("proxy-logs")
    assert docker_util.container_exists("daedalus-api")
    assert docker_util.container_exists("daedalus-web-app-db")
    assert docker_util.container_exists("daedalus-web-app")
    assert docker_util.container_exists("daedalus-proxy")

    # ignore SSL
    session = requests.Session()
    session.verify = False
    res = session.get("https://localhost", verify=False)

    assert res.status_code == 200

    constellation.obj.destroy()

    assert not docker_util.network_exists("daedalus")
    assert not docker_util.volume_exists("daedalus-data")
    assert not docker_util.volume_exists("proxy-logs")
    assert not docker_util.container_exists("daedalus-api")
    assert not docker_util.container_exists("daedalus-web-app-db")
    assert not docker_util.container_exists("daedalus-web-app")
    assert not docker_util.container_exists("daedalus-proxy")
