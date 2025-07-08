import pytest

from src.daedalus_deploy.config import DaedalusConfig


@pytest.fixture
def cfg():
    return DaedalusConfig("config", "fakeproxy")


def test_base_config(cfg):
    assert cfg.path == "config"
    assert cfg.vault.url is None
    assert cfg.network == "daedalus"
    assert cfg.container_prefix == "daedalus"
    assert cfg.volumes["daedalus-redis"] == "daedalus-redis"
    assert cfg.volumes["daedalus-model-results"] == "daedalus-model-results"
    assert cfg.volumes["daedalus-data"] == "daedalus-data"
    assert cfg.volumes["proxy-logs"] == "proxy-logs"
    assert cfg.volumes["daedalus-tls"] == "daedalus-tls"

def test_redis(cfg):
    assert cfg.redis_ref.repo == "library"
    assert cfg.redis_ref.name == "redis"


def test_api(cfg):
    assert cfg.api_queue_id == "daedalus-queue"
    assert cfg.api_number_of_workers == 1
    assert cfg.api_ref.repo == "mrcide"
    assert cfg.api_ref.name == "daedalus.api"
    assert cfg.api_port == 8001


def test_web_app_db(cfg):
    assert cfg.web_app_db_ref.repo == "ghcr.io/jameel-institute"
    assert cfg.web_app_db_ref.name == "daedalus-web-app-db"
    assert cfg.web_app_db_port == 5432
    assert cfg.web_app_db_data_location == "/pgdata"
    assert cfg.web_app_db_postgres_user == "daedalus-web-app-user"
    assert cfg.web_app_db_postgres_password == "changeme"


def test_web_app(cfg):
    assert cfg.web_app_ref.repo == "ghcr.io/jameel-institute"
    assert cfg.web_app_ref.name == "daedalus-web-app"
    assert cfg.web_app_port == 3000


def test_proxy(cfg):
    assert cfg.proxy_ref.repo == "ghcr.io/jameel-institute"
    assert cfg.proxy_ref.name == "daedalus-proxy"
    assert cfg.proxy_host == "localhost"
    assert cfg.proxy_port_http == 80
    assert cfg.proxy_port_https == 443
    assert cfg.proxy_logs_location == "/var/log/nginx"
    assert cfg.ssl is False
