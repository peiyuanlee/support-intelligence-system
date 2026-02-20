#!/bin/bash

# Start Zookeeper
~/kafka/bin/zookeeper-server-start.sh ~/kafka/config/zookeeper.properties &
ZOOKEEPER_PID=$!
echo "Zookeeper started with PID: $ZOOKEEPER_PID"

# Wait for Zookeeper to start
sleep 5

# Start Kafka
~/kafka/bin/kafka-server-start.sh ~/kafka/config/server.properties &
KAFKA_PID=$!
echo "Kafka started with PID: $KAFKA_PID"

echo "Kafka is ready!"
echo "To stop: kill $ZOOKEEPER_PID $KAFKA_PID"