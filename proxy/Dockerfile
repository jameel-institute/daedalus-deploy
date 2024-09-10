FROM nginx:stable

# Clear out default configuration
RUN rm /etc/nginx/conf.d/default.conf

VOLUME /var/log/nginx

COPY proxy/nginx.conf.template /etc/nginx/nginx.conf.template
COPY proxy/bin /usr/local/bin
COPY proxy/ssl/dhparam.pem /run/proxy/dhparam.pem

ENTRYPOINT ["/usr/local/bin/reverse-proxy"]
