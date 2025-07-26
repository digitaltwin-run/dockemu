FROM nginx:alpine

WORKDIR /usr/share/nginx/html

COPY . .

# Configure nginx to serve the frontend
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
