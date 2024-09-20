import constellation
from constellation import config


class DaedalusConfig:
    def __init__(self, path, config_name=None, options=None):
        dat = config.read_yaml(f"{path}/daedalus.yml")
        dat = config.config_build(path, dat, config_name, options=options)
        self.path = path
        self.data = dat
        self.vault = config.config_vault(dat, ["vault"])
        self.network = config.config_string(dat, ["docker", "network"])
        self.container_prefix = config.config_string(dat, ["docker", "prefix"])

        self.containers = {"api": "api", "web-app-db": "web-app-db", "web-app": "web-app", "proxy": "proxy"}

        self.volumes = {
          "daedalus-redis": "daedalus-redis",
          "daedalus-model-results": "daedalus-model-results",
          "daedalus-data": "daedalus-data",
          "proxy-logs": "proxy-logs"
        }

        # redis
        self.redis_ref = self.get_image_reference("redis", dat)

        # api
        self.api_ref = self.get_image_reference("api", dat)
        self.api_port = config.config_integer(dat, ["api", "port"])
        self.api_queue_id = config.config_string(dat, ["api", "queue_id"])
        self.api_number_of_workers = config.config_integer(dat, ["api", "number_of_workers"])

        # web_app_db
        db_key = "web_app_db"
        self.web_app_db_ref = self.get_image_reference(db_key, dat)
        self.web_app_db_port = config.config_integer(dat, [db_key, "port"])
        self.web_app_db_data_location = config.config_string(dat, [db_key, "data_location"])
        self.web_app_db_postgres_user = config.config_string(dat, [db_key, "postgres", "user"])
        self.web_app_db_postgres_password = config.config_string(dat, [db_key, "postgres", "password"])

        # web_app
        self.web_app_ref = self.get_image_reference("web_app", dat)
        self.web_app_port = config.config_integer(dat, ["web_app", "port"])

        # proxy
        proxy_key = "proxy"
        self.proxy_ref = self.get_image_reference(proxy_key, dat)
        self.proxy_host = config.config_string(dat, [proxy_key, "host"])
        self.proxy_port_http = config.config_integer(dat, [proxy_key, "port_http"])
        self.proxy_port_https = config.config_integer(dat, [proxy_key, "port_https"])
        self.proxy_logs_location = config.config_string(dat, [proxy_key, "logs_location"])

        if "ssl" in dat["proxy"]:
            self.proxy_ssl_certificate = config.config_string(dat, [proxy_key, "ssl", "certificate"])
            self.proxy_ssl_key = config.config_string(dat, [proxy_key, "ssl", "key"])
            self.ssl = True
        else:
            self.ssl = False

    def get_image_reference(self, config_section, dat):
        repo = config.config_string(dat, [config_section, "image", "repo"])
        name = config.config_string(dat, [config_section, "image", "name"])
        tag = config.config_string(dat, [config_section, "image", "tag"])
        return constellation.ImageReference(repo, name, tag)
