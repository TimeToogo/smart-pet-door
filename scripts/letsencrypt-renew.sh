#!/bin/bash

# Lets encrypt certificate renewal script
# Required:
#  - miniupnpc (with UPnP enalbed lan router)
#  - certbot

set -e

DOMAIN_NAMES=$1
NOTIFICATION_EMAIL=$2

RENEWAL_TLS_SNI_PORT=22443
RENEWAL_HTTP_PORT=22080
RENEWAL_CERTIFICATE_PATH="$(dirname $(realpath $0))/../data/certs"

if [[ -z "$DOMAIN_NAMES" ]] || [[ -z "$NOTIFICATION_EMAIL" ]];
then
    echo "usage $0 [domain names (csv)] [notification email]"
    exit 1
fi

echo "Mapping external ports (80, 443) to internal ports ($RENEWAL_TLS_SNI_PORT, $RENEWAL_HTTP_PORT) using UPnP"
upnpc -e "letsencrypt-renew-tls" -r $RENEWAL_TLS_SNI_PORT 443 tcp
upnpc -e "letsencrypt-renew-http" -r $RENEWAL_HTTP_PORT 80 tcp

cleanup() {
    echo "Removing UPnP port mappings"
    upnpc -d 443 tcp
    upnpc -d 80 tcp
}

trap cleanup EXIT

echo "Renewing letsencrypt certificates..."
mkdir -p $RENEWAL_CERTIFICATE_PATH/logs
mkdir -p $RENEWAL_CERTIFICATE_PATH/work
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --force-renewal \
    --email $NOTIFICATION_EMAIL \
    --tls-sni-01-port $RENEWAL_TLS_SNI_PORT \
    --http-01-port $RENEWAL_HTTP_PORT \
    --domains $DOMAIN_NAMES \
    --config-dir $RENEWAL_CERTIFICATE_PATH \
    --work-dir $RENEWAL_CERTIFICATE_PATH/work \
    --logs-dir $RENEWAL_CERTIFICATE_PATH/logs

echo "Done"