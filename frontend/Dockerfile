FROM php:8.2-apache

# Install required packages
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Set working directory
WORKDIR /var/www/html

# Copy PHP files and static assets
COPY frontend/index.php /var/www/html/
COPY frontend/generate-config.php /var/www/html/
COPY frontend/style.css /var/www/html/
COPY frontend/app.js /var/www/html/
COPY frontend/js/ /var/www/html/js/

# Copy .env file for PHP to read
COPY .env /var/www/html/.env

# Create js directory if it doesn't exist
RUN mkdir -p /var/www/html/js

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Create Docker-specific config generator script
RUN echo '<?php' > /var/www/html/docker-config.php && \
    echo 'require_once "generate-config.php";' >> /var/www/html/docker-config.php && \
    echo '$generator = new ConfigGenerator("./.env", "./js/config.js");' >> /var/www/html/docker-config.php && \
    echo '$generator->generate();' >> /var/www/html/docker-config.php && \
    echo '?>' >> /var/www/html/docker-config.php

# Create startup script to ensure config is generated
RUN echo '#!/bin/bash' > /usr/local/bin/docker-entrypoint.sh && \
    echo 'set -e' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'cd /var/www/html' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Generating configuration from Docker environment..."' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'php docker-config.php' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'echo "Configuration generated successfully"' >> /usr/local/bin/docker-entrypoint.sh && \
    echo 'exec apache2-foreground' >> /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80

CMD ["/usr/local/bin/docker-entrypoint.sh"]
