import constellation
import constellation.docker_util as docker_util
import constellation.vault as vault


class DaedalusConstellation:
    def __init__(self, cfg, use_vault):
        # resolve secrets early on start so we can use them in container definition
        if use_vault:
          vault.resolve_secrets(cfg, cfg.vault.client())

        # 1. api
        api = constellation.ConstellationContainer("api", cfg.api_ref)

        # 2. web_app_db
        db_user = cfg.web_app_db_postgres_user
        db_password = cfg.web_app_db_postgres_password
        web_app_db_env = {
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": db_password,
        }
        web_app_db_mounts = [constellation.ConstellationMount("daedalus-data", cfg.web_app_db_data_location)]
        web_app_db = constellation.ConstellationContainer(
            "web-app-db", cfg.web_app_db_ref, configure=self.db_configure, environment=web_app_db_env,
            mounts=web_app_db_mounts)

        # 3. web_app
        db_url = "postgresql://{}:{}@daedalus-web-app-db:{}/daedalus-web-app".format(db_user, db_password, cfg.web_app_db_port)
        web_app_env = {
            "DATABASE_URL": db_url,
            "NUXT_R_API_BASE": "http://daedalus-api:{}/".format(cfg.api_port)
        }
        web_app = constellation.ConstellationContainer("web-app", cfg.web_app_ref, environment=web_app_env)

        # 4. proxy
        proxy_ports = [cfg.proxy_port_http, cfg.proxy_port_https]
        proxy_mounts = [constellation.ConstellationMount("proxy-logs", cfg.proxy_logs_location)]
        daedalus_app_url = "http://{}-{}:{}".format(cfg.container_prefix, web_app.name, cfg.web_app_port)
        proxy = constellation.ConstellationContainer(
                "proxy", cfg.proxy_ref, ports=proxy_ports, configure=self.proxy_configure,
                mounts=proxy_mounts,
                args=[cfg.proxy_host, cfg.proxy_ref.name, daedalus_app_url])

        containers = [api, web_app_db, web_app, proxy]

        obj = constellation.Constellation("daedalus", cfg.container_prefix,
                                          containers,
                                          cfg.network, cfg.volumes,
                                          data=cfg)
        self.cfg = cfg
        self.obj = obj

    def start(self, args):
        self.obj.start(**args)

    def db_configure(self, container, cfg):
        print("[web-app-dn] Waiting for db")
        args = ["wait-for-db"]
        docker_util.exec_safely(container, args)

    def proxy_configure(self, container, cfg):
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
