FROM nginx:stable

# Clear out existing configuration
# TODO: need this?
RUN rm /etc/nginx/conf.d/default.conf
RUN rm /usr/share/nginx/html -rf

VOLUME /var/log/nginx

COPY proxy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY proxy/bin /usr/local/bin
COPY proxy/ssl/dhparam.pem /run/proxy/dhparam.pem

ENTRYPOINT ["/usr/local/bin/reverse-proxy"]
