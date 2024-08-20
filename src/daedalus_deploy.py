import time
import os

import docker
import json
import constellation
import constellation.config as config
import constellation.docker_util as docker_util

def get_image_reference(config_section, dat):
    repo = config.config_string(
                dat, [config_section, "image", "repo"])
    name = config.config_string(
        dat, [config_section, "image", "name"])
    tag = config.config_string(
        dat, [config_section, "image", "tag"])
    return self.proxy_ref = constellation.ImageReference(repo, name, tag)

class DaedalusConfig:
    def __init__(self, path, config_name=None, options=None):
        dat = config.read_yaml("{}/daedalus.yml".format(path))
        dat = config.config_build(path, dat, config_name, options=options)
        self.path = path
        self.data = dat
        self.vault = config.config_vault(dat, ["vault"])
        self.network = config.config_string(dat, ["docker", "network"])
        self.container_prefix = config.config_string(dat, ["docker", "prefix"])

        # TODO: do we need this??
        self.containers = {
            "api": "api",
            "web_app_db": "web_app_db",
            "web_app": "web_app",
            "proxy": "proxy"
        }

        self.volumes = {
            "daedalus_data": "daedalus_data"
        }

        # api
        self.api_ref = get_image_reference("api")
        self.api_port = config.config_string(dat, ["proxy", "port"])

        # web_app_db
        self.web_app_db_ref = get_image_reference("web_app_db")
        self.web_app_db_port = config.config_string(dat, ["web_app_db", "port"])
        self.web_app_db_data_location = config.config_string(dat, ["web_app_db", "data_location"])

        # web_app
        self.web_app_ref = get_image_reference("web_app")
        self.web_app_port = config.config_string(dat, ["web_app", "port"])

        # proxy
        self.proxy_ref = get_image_reference("proxy")
        self.proxy_host = config.config_string(dat, ["proxy", "host"])
        self.proxy_port_http = config.config_integer(dat,
                                                     ["proxy", "port_http"])
        self.proxy_port_https = config.config_integer(dat,
                                                      ["proxy", "port_https"])
        if "ssl" in dat["proxy"]:
            self.proxy_ssl_certificate = config.config_string(dat,
                                                              ["proxy",
                                                               "ssl",
                                                               "certificate"])
            self.proxy_ssl_key = config.config_string(dat,
                                                      ["proxy",
                                                       "ssl",
                                                       "key"])
            self.ssl = True
        else:
            self.ssl = False


def daedalus_constellation(cfg):
    # 1. api
    api = constellation.ConstellationContainer("api", cfg.api_ref)

    # 2. web_app_db
    # TODO: non-default db credentials
    web_app_db_mounts = [constellation.ConstellationMount("daedalus_data", cfg.web_app_db_data_location)]
    # TODO: include volume in db docker file
    web_app_db_env = {"PGDATA", cfg.web_app_db_data_location}
    web_app_db = constellation.ConstellationContainer(
        "web_app_db", cfg.web_app_db_ref, environment=web_app_db_env, mounts=web_app_db_mounts)

    # 3. web_app
    web_app_env = {
        "DATABASE_URL": "postgresql://daedalus-web-app-user:changeme@daedalus-web-app-db:{}/daedalus-web-app".format(cfg.web_app_db_port),
        "NUXT_R_API_BASE": "http://daedalus-api:{}/".format(cfg.api_port)
    }
    web_app = constellation.ConstellationContainer("web_app", cfg.web_app_ref, environment=web_app_env)

    # 4. proxy
    proxy_ports = [cfg.proxy_port_http, cfg.proxy_port_https]
    proxy = constellation.ConstellationContainer(
            "proxy", cfg.proxy_ref, ports=proxy_ports, configure=proxy_configure,
            args=[cfg.proxy_host, web_app.name])

    containers = [api, web_app_db, web_app, proxy]

    obj = constellation.Constellation("daedalus", cfg.container_prefix,
                                      containers,
                                      cfg.network, cfg.volumes,
                                      data=cfg, vault_config=cfg.vault)
    return obj


def daedalus_start(obj, args):
    obj.start(**args)

def proxy_configure(container, cfg):
    print("[proxy] Configuring proxy")
    if cfg.ssl:
        print("Copying ssl certificate and key into proxy")
        docker_util.string_into_container(cfg.proxy_ssl_certificate, container,
                                          "/run/proxy/certificate.pem")
        docker_util.string_into_container(cfg.proxy_ssl_key, container,
                                          "/run/proxy/key.pem")
    else:
        print("Generating self-signed certificates for proxy")
        args = ["/usr/local/bin/build-self-signed-certificate", "/run/proxy",
                "GB", "London", "IC", "jameel-institute", cfg.proxy_host]
        docker_util.exec_safely(container, args)
