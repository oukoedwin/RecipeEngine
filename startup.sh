#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- Step 1: Install and start PostgreSQL ---
echo "Installing and starting PostgreSQL (if not already installed)..."
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL not found, installing via Homebrew..."
    brew install postgresql
else
    echo "PostgreSQL already installed."
fi

# Start PostgreSQL service
brew services start postgresql

# --- Step 2: Create database and user ---
echo "Setting up PostgreSQL user and database..."

psql postgres <<EOF
DROP DATABASE IF EXISTS recipe_db;
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'edwin') THEN
        CREATE USER edwin WITH PASSWORD 'edwin';
    END IF;
END
\$\$;
CREATE DATABASE recipe_db OWNER edwin;
GRANT ALL PRIVILEGES ON DATABASE recipe_db TO edwin;
EOF

echo "Database 'recipe_db' and user 'edwin' have been created."

# --- Step 3: Django migrations ---
echo "Running Django migrations..."
python3 manage.py makemigrations recipes accounts social
python3 manage.py migrate

# --- Step 4: Create Django superuser ---
echo "Creating Django superuser..."
# Using environment variables to auto-create the superuser
export DJANGO_SUPERUSER_USERNAME=edwin
export DJANGO_SUPERUSER_PASSWORD=edwin
export DJANGO_SUPERUSER_EMAIL=edwin@example.com

python3 manage.py createsuperuser --noinput || echo "Superuser may already exist."

# --- Step 6: Run the Django development server ---
echo "Starting Django development server..."
python3 manage.py runserver
