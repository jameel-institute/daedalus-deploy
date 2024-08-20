FROM nginx:stable

# Clear out existing configuration
RUN rm /etc/nginx/conf.d/default.conf
RUN rm /usr/share/nginx/html -rf

# TODO: include these in constellation config
VOLUME /var/log/nginx
# location for certs
VOLUME /run/proxy

COPY proxy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY proxy/bin /usr/local/bin
COPY proxy/ssl/dhparam.pem /run/proxy/dhparam.pem

# TODO: why is this needed?
COPY --from=0 /app/dist /usr/share/nginx/html

ENTRYPOINT ["/usr/local/bin/reverse-proxy"]
