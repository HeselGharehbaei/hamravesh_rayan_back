# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git \
       gcc \
       python3-dev \
       default-libmysqlclient-dev \
       build-essential \
       libpq-dev \
       pkg-config \
       libmariadb-dev-compat \
       libmariadb-dev \
       tmux \
       supervisor \
       vim \
    && rm -rf /var/lib/apt/lists/*

# Set up Django project directory
WORKDIR /code

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the Docker image
COPY . /code/

# Collect static files
# RUN python manage.py collectstatic --noinput

# Configure Nginx
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/conf.d/default.conf

# Copy Supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port 8000 (Gunicorn)
EXPOSE 8000

# Run Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
