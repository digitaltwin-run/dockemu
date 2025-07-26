FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Copy static files
COPY index.html .
COPY style.css .
COPY app.js .

# Copy configuration files
COPY .env .
COPY config.json .
COPY js/ ./js/

# Configure nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
