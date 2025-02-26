#!/bin/bash

# This script checks that the sysctl are correctly set on an EKS cluster

function check_sysctl(){
    SSH_CMD=$1
    KEY=$2
    VALUE=$3

    CURRENT=$($SSH_CMD 'sudo sysctl -a 2>/dev/null' | grep "^${KEY}" | cut -d "=" -f 2 | xargs)

    if [ "$CURRENT" != "$VALUE" ]
    then
      exit 1
    fi
}

# Export all instances
aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=running \
  --output yaml > instances.yaml

INTERNAL_DNS=$(kubectl get nodes -A | tail -n+2 | awk '{print $1}')

for DNS in $INTERNAL_DNS;
do
  # Figure out external dns
  DNS_QUERY=".Reservations[].Instances | flatten | map(select(.PrivateDnsName==\"${DNS}\"))[].PublicDnsName"
  echo $DNS_QUERY
  EXTERNAL_DNS=$(yq "$DNS_QUERY" instances.yaml)

  echo "=========================================="
  echo "Internal DNS: ${DNS}"
  echo "Using external DNS: ${EXTERNAL_DNS}"
  SSH_CMD="ssh -o StrictHostKeyChecking=no ubuntu@$EXTERNAL_DNS"

  # Setting the sysctl properties
  echo "Setting values"
  $SSH_CMD 'sudo sysctl fs.inotify.max_user_watches=655360'
  $SSH_CMD 'sudo sysctl fs.inotify.max_user_instances=1280'

  # To check the settings
  echo "Checking values"
  check_sysctl $SSH_CMD "fs.inotify.max_user_watches" "65536"
  check_sysctl $SSH_CMD "fs.inotify.max_user_instances" "1280"
  echo "=========================================="
done

rm instances.yaml
