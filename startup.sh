#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

env=${1:-"development"}

$cmd = ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    $cmd = "brew" 
else if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    $cmd = "sudo apt-get"
fi

# --- Step 1: Install and start PostgreSQL ---
echo "Installing and starting PostgreSQL (if not already installed)..."
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL not found, installing via Homebrew..."
    $cmd install postgresql
else
    echo "PostgreSQL already installed."
fi

if $env == "production"
then
    # Install nginx if not installed
    if ! command -v nginx &> /dev/null
    then
        echo "Nginx not found, installing via Homebrew..."
        $cmd install nginx 
        cat ./nginx.conf > /etc/nginx/sites-available/recipe_app
        sudo ln -s /etc/nginx/sites-available/recipe_app /etc/nginx/sites-enabled/
        sudo systemctl restart nginx
    else
        echo "Nginx already installed."
    fi
fi

# Start PostgreSQL service
$cmd services start postgresql

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
if $env == "production"
then
    echo "Starting Django production server..."
    python3 manage.py collectstatic 
    Read ./gunicorn.service and write to /etc/systemd/system/gunicorn.service
    cat ./gunicorn.service > /etc/systemd/system/gunicorn.service
    gunicorn --bind 0.0.0.0:8000 recipe_project.wsgi:application 
else
    echo "Starting Django development server..."
    python3 manage.py runserver
fi