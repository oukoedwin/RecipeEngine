#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

env=${1:-"development"}

# Detect OS and set install / service commands
cmd=""
install_cmd=""
service_start_cmd=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    cmd="brew"
    install_cmd="brew install"
    service_start_cmd="brew services start"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    cmd="apt"
    install_cmd="sudo apt-get install -y"
    service_start_cmd="sudo systemctl start"
else
    install_cmd="echo 'Unknown OS: please install dependencies manually'"
    service_start_cmd="echo 'Cannot start services automatically on this OS'"
fi

# --- Step 0: Set up Python virtual environment and install dependencies ---
echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# --- Step 1: Install and start PostgreSQL ---
echo "Installing and starting PostgreSQL (if not already installed)..."
if ! command -v psql &> /dev/null
then
    echo "PostgreSQL not found, installing..."
    $install_cmd postgresql
else
    echo "PostgreSQL already installed."
fi

if [[ "$env" == "production" ]]
then
    # Install nginx if not installed
    if ! command -v nginx &> /dev/null
    then
        echo "Nginx not found, installing..."
        $install_cmd nginx
        sudo cp recipe/nginx.conf /etc/nginx/sites-available/recipe_app || true
        sudo ln -sf /etc/nginx/sites-available/recipe_app /etc/nginx/sites-enabled/
        sudo systemctl restart nginx || true
    else
        echo "Nginx already installed."
    fi
fi
# Start PostgreSQL service
$service_start_cmd postgresql || true

# --- Step 2: Create database and user ---
echo "Setting up PostgreSQL user and database..."

psql postgres <<EOF
DROP DATABASE IF EXISTS recipe_db;
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'edwin') THEN
        CREATE USER edwin WITH PASSWORD 'edwin' CREATEDB;
    END IF;
END
\$\$;
-- CREATEDB is needed so pytest-django/manage.py test can create the test_recipe_db
-- database; ALTER unconditionally so pre-existing installs pick it up too.
ALTER USER edwin CREATEDB;
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
if [[ "$env" == "production" ]]
then
    echo "Starting Django production server..."
    python3 manage.py collectstatic 
    # Install/copy systemd service for gunicorn (requires sudo)
    sudo cp recipe/gunicorn.service /etc/systemd/system/gunicorn.service || true
    sudo systemctl daemon-reload || true
    sudo systemctl enable --now gunicorn.service || sudo systemctl restart gunicorn.service || true
    gunicorn --bind 0.0.0.0:8000 recipe.wsgi:application &
else
    echo "Starting Django development server..."
    python3 manage.py runserver
fi