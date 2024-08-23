from constellation import docker_util

from src.daedalus_deploy.config import DaedalusConfig
from src.daedalus_deploy.daedalus_constellation import DaedalusConstellation


def test_start_daedalus():
    # use a config that doesn't involve vault secrets
    cfg = DaedalusConfig("config", "fakeproxy")
    constellation = DaedalusConstellation(cfg, False)
    constellation.start({})
    constellation.obj.status()

    assert docker_util.network_exists("daedalus")
    assert docker_util.volume_exists("daedalus-data")
    assert docker_util.volume_exists("proxy-logs")
    assert docker_util.container_exists("daedalus-api")
    assert docker_util.container_exists("daedalus-web-app-db")
    assert docker_util.container_exists("daedalus-web-app")
    assert docker_util.container_exists("daedalus-proxy")

    constellation.obj.destroy()

    assert not docker_util.network_exists("daedalus")
    assert not docker_util.volume_exists("daedalus-data")
    assert not docker_util.volume_exists("proxy-logs")
    assert not docker_util.container_exists("daedalus-api")
    assert not docker_util.container_exists("daedalus-web-app-db")
    assert not docker_util.container_exists("daedalus-web-app")
    assert not docker_util.container_exists("daedalus-proxy")
