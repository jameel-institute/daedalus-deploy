import constellation
from constellation import docker_util, vault


class DaedalusConstellation:
    def __init__(self, cfg, use_vault):
        # resolve secrets early (before start) so we can use them in
        # container definition
        if use_vault:
            vault.resolve_secrets(cfg, cfg.vault.client())

        # 1. redis
        redis_mounts = [constellation.ConstellationMount("daedalus-redis", "/data")]
        redis = constellation.ConstellationContainer(
          "redis",
          cfg.redis_ref,
          mounts=redis_mounts
        )

        # 2. api configure
        api_env = {
          "DAEDALUS_QUEUE_ID": cfg.api_queue_id,
          "REDIS_CONTAINER_NAME": "daedalus-redis"
        }
        api_configure = constellation.ConstellationContainer(
          "api-configure",
          cfg.api_ref,
          entrypoint="/usr/local/bin/daedalus.api.configure",
          environment=api_env
        )

        # 2. api worker
        api_mounts = [constellation.ConstellationMount("daedalus-model-results", "/daedalus/results")]
        # TODO: make as many of these as number of workers!! Use ConstellationService
        api_worker = constellation.ConstellationContainer(
          "api-worker",
          cfg.api_ref,
          environment=api_env,
          mounts=api_mounts,
          entrypoint="/usr/local/bin/daedalus.api.worker"
        )

        # 3. api
        api = constellation.ConstellationContainer(
          "api",
          cfg.api_ref,
          environment=api_env,
          mounts=api_mounts,
          entrypoint="/usr/local/bin/daedalus.api"
        )

        # 4. web_app_db
        db_user = cfg.web_app_db_postgres_user
        db_password = cfg.web_app_db_postgres_password
        web_app_db_env = {
            "POSTGRES_USER": db_user,
            "POSTGRES_PASSWORD": db_password,
        }
        web_app_db_mounts = [constellation.ConstellationMount("daedalus-data", cfg.web_app_db_data_location)]
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
        proxy_mounts = [constellation.ConstellationMount("proxy-logs", cfg.proxy_logs_location)]
        daedalus_app_url = f"http://{cfg.container_prefix}-{web_app.name}:{cfg.web_app_port}"
        proxy = constellation.ConstellationContainer(
            "proxy",
            cfg.proxy_ref,
            ports=proxy_ports,
            configure=self.proxy_configure,
            mounts=proxy_mounts,
            args=[cfg.proxy_host, cfg.proxy_ref.name, daedalus_app_url],
        )

        containers = [redis, api_configure, api_worker, api, web_app_db, web_app, proxy]

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

    def proxy_configure(self, container, cfg):
        if cfg.ssl:
            print("Copying ssl certificate and key into proxy")
            docker_util.string_into_container(cfg.proxy_ssl_certificate, container, "/run/proxy/certificate.pem")
            docker_util.string_into_container(cfg.proxy_ssl_key, container, "/run/proxy/key.pem")
        else:
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

    #def rrq_configure(self, container, cfg):
        # The container here is the redis container - after it's running we attempt to configure the queue by running
        # the api with the configure entrypoint - the entrypoint will fail if the queue is already configured, but
        # that shouldn't throw an exception here
        # TODO: SINCE THIS *DOESN'T THROW AN EXCEPTION WE SHOULD JUST BE ABLE TO INCLUDE THE CONFIGURE CONTAINER IN THE
        # CONSTELLATION!! THen don't need to worry about removing it...
        #print("Configuring rrq queue")
        #env = {
        #  "DAEDALUS_QUEUE_ID": cfg.api_queue_id,
        #  "REDIS_CONTAINER_NAME": "daedalus-redis"
        #}
        #configure_container = constellation.ConstellationContainer(
        #  "api-configure",
        #  cfg.api_ref,
        #  entrypoint="/usr/local/bin/daedalus.api.configure",
        #  environment=env
        #)
        #configure_container.start(cfg.container_prefix, self.obj.network, None)
