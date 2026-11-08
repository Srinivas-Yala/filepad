# Deployment Guide

## Production Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx -y
```

### 2. Clone and Setup Project

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/filepad.git
cd filepad

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R $USER:$USER venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create .env file
cp .env.example .env
nano .env
```

Add your credentials:
```env
DEBUG=False
DJANGO_SECRET_KEY=generate-a-random-secret-key
USE_S3=True
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=your-region
```

### 4. Setup Database

```bash
python3 manage.py makemigrations filepad
python3 manage.py migrate
python3 manage.py createsuperuser  # Optional
```

### 5. Create Systemd Service

Create `/etc/systemd/system/filepad.service`:

```ini
[Unit]
Description=FilePad Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/filepad
EnvironmentFile=/var/www/filepad/.env
ExecStart=/var/www/filepad/venv/bin/gunicorn \
    --workers 3 \
    --timeout 120 \
    --bind unix:/var/www/filepad/filepad.sock \
    filepad_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable filepad
sudo systemctl start filepad
sudo systemctl status filepad
```

### 6. Configure Nginx

Create `/etc/nginx/sites-available/filepad`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://unix:/var/www/filepad/filepad.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/filepad/staticfiles/;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/filepad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Setup SSL (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

### 8. Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/filepad
sudo chmod 755 /var/www/filepad
```

## Caddy Alternative

If using Caddy instead of Nginx:

**Caddyfile:**
```
yourdomain.com {
    reverse_proxy unix//var/www/filepad/filepad.sock
}
```

Restart:
```bash
sudo systemctl restart caddy
```

## Update Deployment

```bash
cd /var/www/filepad
git pull
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
sudo systemctl restart filepad
```

## Monitoring

```bash
# Check service status
sudo systemctl status filepad

# View logs
sudo journalctl -u filepad -f

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Backup

```bash
# Backup database
cp /var/www/filepad/db.sqlite3 /backup/db.sqlite3.$(date +%Y%m%d)

# S3 files are automatically backed up by AWS
```

## Security Checklist

- [ ] Set DEBUG=False in production
- [ ] Generate strong DJANGO_SECRET_KEY
- [ ] Use HTTPS (SSL certificate)
- [ ] Keep AWS credentials in .env (never commit)
- [ ] Set proper file permissions
- [ ] Enable firewall (UFW)
- [ ] Regular backups
- [ ] Monitor logs for issues
