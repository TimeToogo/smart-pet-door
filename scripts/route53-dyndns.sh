#!/bin/bash

set -e

HOSTED_ZONE_ID=$1
DOMAIN_NAME=$2

if [[ -z "$HOSTED_ZONE_ID" ]] || [[ -z "$DOMAIN_NAME" ]];
then
    echo "usage $0 [hosted zone id] [domain name]"
    exit 1
fi

echo "Retrieving current IP address..."
CURR_IP="$(curl -sSf https://ipinfo.io/ip)"
echo "Current IP: $CURR_IP"

echo "Updating domain A record $DOMAIN_NAME (hosted zone $HOSTED_ZONE_ID)..."

AWS_PAGER="" aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch "{ \
        \"Comment\": \"Updating record to current IP\", \
        \"Changes\": [{ \
            \"Action\": \"UPSERT\", \
            \"ResourceRecordSet\": { \
                \"Name\": \"$DOMAIN_NAME\", \
                \"Type\": \"A\", \
                \"TTL\": 300, \
                \"ResourceRecords\": [{ \"Value\": \"$CURR_IP\"}] \
            } \
        }] \
    }"

echo "Record updated!"