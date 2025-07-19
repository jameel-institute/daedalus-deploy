import os

import constellation
from constellation import docker_util, vault


class DaedalusConstellation:
    def __init__(self, cfg, use_vault):
        # resolve secrets early (before start) so we can use them in
        # container definition
        if use_vault:
            vault.resolve_secrets(cfg, cfg.vault.client())

        # 1. redis
        redis_mounts = [constellation.ConstellationVolumeMount("daedalus-redis", "/data")]
        redis = constellation.ConstellationContainer("redis", cfg.redis_ref, mounts=redis_mounts)

        # 2. api
        api_env = {"DAEDALUS_QUEUE_ID": cfg.api_queue_id, "REDIS_CONTAINER_NAME": "daedalus-redis"}
        api_mounts = [constellation.ConstellationVolumeMount("daedalus-model-results", "/daedalus/results")]
        api = constellation.ConstellationContainer(
            "api",
            cfg.api_ref,
            environment=api_env,
            mounts=api_mounts,
            configure=self.api_wait,
            entrypoint="/usr/local/bin/daedalus.api",
        )

        # 3. api workers
        api_workers = constellation.ConstellationService(
            "api-worker",
            cfg.api_ref,
            cfg.api_number_of_workers,
            environment=api_env,
            mounts=api_mounts,
            entrypoint="/usr/local/bin/daedalus.api.worker",
        )

        # 4. web_app_db
        db_user = cfg.web_app_db_postgres_user
        db_password = cfg.web_app_db_postgres_password
        web_app_db_env = {
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": db_password,
        }
        web_app_db_mounts = [constellation.ConstellationVolumeMount("daedalus-data", cfg.web_app_db_data_location)]
        web_app_db = constellation.ConstellationContainer(
            "web-app-db",
            cfg.web_app_db_ref,
            configure=self.db_configure,
            environment=web_app_db_env,
            mounts=web_app_db_mounts,
        )

        # 5. web_app
        db_url = (
            f"postgresql://{db_user}:{db_password}@{cfg.web_app_db_ref.name}:{cfg.web_app_db_port}/daedalus-web-app"
        )
        web_app_env = {"DATABASE_URL": db_url, "NUXT_R_API_BASE": f"http://daedalus-api:{cfg.api_port}/"}
        web_app = constellation.ConstellationContainer("web-app", cfg.web_app_ref, environment=web_app_env)

        # 6. proxy
        proxy_ports = [cfg.proxy_port_http, cfg.proxy_port_https]
        proxy_mounts = [
            constellation.ConstellationVolumeMount("proxy-logs", cfg.proxy_logs_location),
            constellation.ConstellationVolumeMount("daedalus-tls", "/run/proxy"),
        ]
        daedalus_app_url = f"http://{cfg.container_prefix}-{web_app.name}:{cfg.web_app_port}"
        proxy = constellation.ConstellationContainer(
            "proxy",
            cfg.proxy_ref,
            ports=proxy_ports,
            configure=self.proxy_configure,
            mounts=proxy_mounts,
            args=[cfg.proxy_host, cfg.proxy_ref.name, daedalus_app_url],
        )

        # 7. acme-buddy

        acme_buddy_staging = os.environ.get("ACME_BUDDY_STAGING", 0)
        acme_env = {
            "ACME_BUDDY_STAGING": acme_buddy_staging,
            "HDB_ACME_USERNAME": cfg.acme_buddy_hdb_username,
            "HDB_ACME_PASSWORD": cfg.acme_buddy_hdb_password,
        }
        acme_mounts = [
            constellation.ConstellationVolumeMount("daedalus-tls", "/tls"),
            constellation.ConstellationBindMount("/var/run/docker.sock", "/var/run/docker.sock"),
        ]

        acme = constellation.ConstellationContainer(
            "acme-buddy",
            cfg.acme_buddy_ref,
            ports=[cfg.acme_buddy_port],
            mounts=acme_mounts,
            environment=acme_env,
            args=[
                "--domain",
                cfg.proxy_host,
                "--email",
                "reside@imperial.ac.uk",
                "--dns-provider",
                "hdb",
                "--certificate-path",
                "/tls/certificate.pem",
                "--key-path",
                "/tls/key.pem",
                "--account-path",
                "/tls/account.json",
                "--reload-container",
                proxy.name_external(cfg.container_prefix),
            ],
        )

        containers = [redis, api, api_workers, web_app_db, web_app, proxy, acme]

        obj = constellation.Constellation(
            "daedalus", cfg.container_prefix, containers, cfg.network, cfg.volumes, data=cfg
        )
        self.cfg = cfg
        self.obj = obj

    def start(self, args):
        self.obj.start(**args)

    def db_configure(self, container, _):
        print("[web-app-dn] Waiting for db")
        args = ["wait-for-db"]
        docker_util.exec_safely(container, args)

    def api_wait(self, container, _):
        # Give the api a couple of seconds to configure the queue
        print("Waiting for api")
        args = ["sleep", "2"]
        docker_util.exec_safely(container, args)

    def proxy_configure(self, container, cfg):
        if not cfg.ssl:
            print("Generating self-signed certificates for proxy")
            args = [
                "/usr/local/bin/build-self-signed-certificate",
                "/run/proxy",
                "GB",
                "London",
                "IC",
                "jameel-institute",
                cfg.proxy_host,
            ]
            docker_util.exec_safely(container, args)
