#!/bin/bash

set -e

host="10.100.3.10"
port="3306"
user="root"
password="root"
database="scadalts"

echo "Waiting for MySQL at $host:$port to be ready..."

# Wait for MySQL port to be open
until nc -z -v -w30 $host $port; do
  echo "Waiting for database connection..."
  sleep 2
done

echo "MySQL port is open, waiting for database to be ready..."

# Wait for MySQL to accept connections and database to exist
for i in {1..30}; do
  if mysql -h"$host" -P"$port" -u"$user" -p"$password" -e "USE $database" 2>/dev/null; then
    echo "MySQL is ready and database exists!"
    exit 0
  fi
  echo "Attempt $i: MySQL not ready yet..."
  sleep 2
done

echo "ERROR: MySQL did not become ready in time"
exit 1
