#!/bin/bash

set -e

HOSTED_ZONE_ID=$1
DOMAIN_NAME=$2
IP_MODE=$3
LAN_INTERFACE=$4

if [[ -z "$HOSTED_ZONE_ID" ]] || [[ -z "$DOMAIN_NAME" ]] || [[ -z "$IP_MODE" ]];
then
    echo "usage $0 [hosted zone id] [domain name] [mode: wan|lan]"
    exit 1
fi

echo "Retrieving current IP address..."
if [[ "$IP_MODE" == "wan" ]];
then
	CURR_IP="$(curl -sSf https://ipinfo.io/ip)"
elif [[ "$IP_MODE" == "lan" ]];
then
	DEFAULT_NETWORK_INTERFACE="$(ip -4 route list | grep 'default via' | head -n1 | grep -Eo 'dev\s\S+' | cut -d' ' -f2)"
	CURR_IP="$(ifconfig $DEFAULT_NETWORK_INTERFACE | grep 'inet ' | awk '{ print $2 }')"
else
	echo "invalid network mode: $IP_MODE"
	exit 1
fi
echo "Current IP: $CURR_IP ($IP_MODE)"

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
