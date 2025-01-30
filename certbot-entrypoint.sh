#!/bin/sh
set -x

if [ ! -d /etc/letsencrypt/live ]; then
  certbot certonly --webroot -w /var/lib/letsencrypt \
    --agree-tos --no-eff-email --email nevalions@gmail.com \
    -d statsboard.ru -d www.statsboard.ru -d statsboard.online -d www.statsboard.online
fi

while :; do
  certbot renew --webroot -w /var/lib/letsencrypt --quiet --agree-tos --post-hook "nginx -s reload"
  sleep 12h
done
