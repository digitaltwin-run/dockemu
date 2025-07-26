FROM nginx:alpine

# Copy web files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Copy configuration files
COPY .env /usr/share/nginx/html/
COPY config.json /usr/share/nginx/html/
COPY js/ /usr/share/nginx/html/js/

# Copy nginx template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
