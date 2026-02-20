#!/bin/bash

# Create topics
~/kafka/bin/kafka-topics.sh --create \
  --topic support_tickets \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

~/kafka/bin/kafka-topics.sh --create \
  --topic processed_tickets \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

~/kafka/bin/kafka-topics.sh --create \
  --topic ticket_alerts \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# List topics
~/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092