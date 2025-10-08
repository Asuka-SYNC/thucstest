#!/bin/bash
set -e

# Configurable variables (can be set as environment variables or edited directly)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_ROOT_USER="${DB_ROOT_USER:-root}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-rootpass}"
DB_USER="${DB_USER:-thucs2pl}"
DB_PASSWORD="${DB_PASSWORD:-thucs2plpass}"
DB_NAME="${DB_NAME:-thucs2pl_db}"

SQL="
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
"

echo "Connecting to MariaDB at $DB_HOST:$DB_PORT as $DB_ROOT_USER..."
mariadb -h"$DB_HOST" -P"$DB_PORT" -u"$DB_ROOT_USER" -p"$DB_ROOT_PASSWORD" -e "$SQL"

echo "User '$DB_USER' created and granted privileges on database '$DB_NAME'."
