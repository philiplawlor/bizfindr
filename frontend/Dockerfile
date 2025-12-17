# Use Nginx as a lightweight web server for static files
FROM nginx:alpine

# Remove default Nginx configuration
RUN rm -rf /usr/share/nginx/html/*

# Copy static frontend files to Nginx
COPY static/ /usr/share/nginx/html/static/
COPY templates/ /usr/share/nginx/html/templates/

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create a non-root user
RUN addgroup -g 1001 -S nginxuser
RUN adduser -S nginxuser -u 1001

# Change ownership of the web directory
RUN chown -R nginxuser:nginxuser /usr/share/nginx/html
RUN chown -R nginxuser:nginxuser /var/cache/nginx
RUN chown -R nginxuser:nginxuser /var/log/nginx
RUN chown -R nginxuser:nginxuser /etc/nginx/conf.d
RUN touch /var/run/nginx.pid
RUN chown -R nginxuser:nginxuser /var/run/nginx.pid

# Switch to non-root user
USER nginxuser

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
