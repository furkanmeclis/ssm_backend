#!/bin/bash
# Stop nginx
docker-compose stop nginx

# Run certbot renewal
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt -v /var/www/certbot:/var/www/certbot certbot/certbot certonly --standalone -d sinavsorularimerkezi.com -d api.sinavsorularimerkezi.com --force-renewal

# Start nginx
docker-compose start nginx
