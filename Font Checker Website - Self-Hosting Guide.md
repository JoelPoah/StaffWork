# Font Checker Website - Self-Hosting Guide

This guide provides instructions on how to host the Font Checker website on your own infrastructure. By self-hosting, you'll have complete control over the application and your data.

## Requirements

To host the Font Checker website, you'll need:

1. A server or hosting environment with:
   - Python 3.9 or higher
   - Ability to install Python packages
   - At least 512MB RAM
   - Approximately 100MB disk space

2. Basic familiarity with command-line operations

## Hosting Options

Here are several recommended options for hosting the Font Checker website:

### Option 1: Traditional Web Hosting with Python Support

Many web hosting providers offer Python support. Look for hosts that support:
- Python 3.9+
- WSGI applications
- The ability to install custom Python packages

**Recommended providers:**
- PythonAnywhere
- A2 Hosting
- DreamHost (with Python support)

### Option 2: Cloud Platform Services

Cloud platforms provide scalable, reliable hosting with easy deployment options.

**Recommended services:**
- **Google Cloud App Engine**: Fully managed, scales automatically
- **AWS Elastic Beanstalk**: Easy deployment and management
- **Microsoft Azure App Service**: Integrated with other Azure services
- **DigitalOcean App Platform**: Simple deployment with reasonable pricing

### Option 3: Self-Managed VPS or Dedicated Server

For complete control, you can use a Virtual Private Server (VPS) or dedicated server.

**Recommended providers:**
- DigitalOcean Droplets
- Linode
- AWS EC2
- Vultr

## Installation Instructions

### Local Testing

Before deploying to production, test the application locally:

1. Extract the `font_checker_website.zip` file to a directory on your computer
2. Open a terminal/command prompt and navigate to the extracted directory
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open a web browser and navigate to `http://localhost:5000` to verify it works

### Production Deployment

#### Option 1: Traditional Web Hosting

1. Upload the extracted files to your web hosting account
2. Set up a Python virtual environment (if supported)
3. Install dependencies using `pip install -r requirements.txt`
4. Configure your web server to run the WSGI application
   - For Apache with mod_wsgi, create a `.htaccess` file with appropriate directives
   - For Nginx, configure it to proxy requests to Gunicorn

#### Option 2: VPS or Dedicated Server

1. SSH into your server
2. Install Python and required packages:
   ```
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   ```
3. Create a directory for the application:
   ```
   mkdir -p /var/www/font_checker
   ```
4. Upload and extract the zip file to this directory
5. Create a virtual environment:
   ```
   cd /var/www/font_checker
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```
6. Create a systemd service file to run the application:
   ```
   sudo nano /etc/systemd/system/font_checker.service
   ```
   
   Add the following content:
   ```
   [Unit]
   Description=Font Checker Web Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/font_checker
   Environment="PATH=/var/www/font_checker/venv/bin"
   ExecStart=/var/www/font_checker/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 app_production:app

   [Install]
   WantedBy=multi-user.target
   ```

7. Configure Nginx as a reverse proxy:
   ```
   sudo nano /etc/nginx/sites-available/font_checker
   ```
   
   Add the following content:
   ```
   server {
       listen 80;
       server_name your_domain.com;  # Replace with your domain

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. Enable the site and restart services:
   ```
   sudo ln -s /etc/nginx/sites-available/font_checker /etc/nginx/sites-enabled
   sudo systemctl start font_checker
   sudo systemctl enable font_checker
   sudo systemctl restart nginx
   ```

#### Option 3: Google Cloud App Engine

1. Install the Google Cloud SDK
2. Navigate to the extracted directory
3. Deploy using:
   ```
   gcloud app deploy app.yaml
   ```

#### Option 4: Docker Deployment

For containerized deployment, create a `Dockerfile` in the root directory:

```
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD exec gunicorn --bind :$PORT app_production:app
```

Then build and run the Docker container:
```
docker build -t font-checker .
docker run -p 8080:8080 font-checker
```

## Security Considerations

1. **HTTPS**: Always use HTTPS in production. Set up SSL certificates using Let's Encrypt.
2. **File Uploads**: The application handles file uploads. Ensure your server has adequate security measures.
3. **Regular Updates**: Keep your server and Python packages updated to patch security vulnerabilities.
4. **Backups**: Regularly back up your application and configuration files.

## Maintenance

1. **Monitoring**: Set up monitoring to track application health and performance.
2. **Logging**: Configure proper logging to troubleshoot issues.
3. **Updates**: Periodically update dependencies by running:
   ```
   pip install --upgrade -r requirements.txt
   ```

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Check if all dependencies are installed
   - Verify Python version compatibility
   - Check file permissions

2. **Upload errors**:
   - Ensure the upload directory is writable
   - Check file size limits in your web server configuration

3. **Slow performance**:
   - Increase the number of Gunicorn workers
   - Consider adding a caching layer

For additional help, refer to the Flask documentation or contact your hosting provider's support team.

## Conclusion

By following this guide, you should be able to successfully host the Font Checker website on your own infrastructure. This gives you complete control over the application and ensures your document processing happens on your own servers.

If you encounter any issues or have questions about self-hosting, please reach out for assistance.
