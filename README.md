# FilePad - Secure Cloud Storage

Password-protected file storage application using Django and AWS S3.

## Features

- 🔐 **Secure Authentication** - Password-based with SHA-256 hashing
- ☁️ **AWS S3 Storage** - Unlimited, persistent cloud storage
- 📁 **File Management** - Upload, download, and delete files
- 🎨 **Clean UI** - Modern, responsive web interface
- 🚀 **Production Ready** - Optimized for deployment

## Tech Stack

- **Backend:** Django 5.0.9 + Django REST Framework
- **Storage:** AWS S3 (via django-storages)
- **Server:** Gunicorn
- **Frontend:** Vanilla JavaScript (no dependencies)
- **Database:** SQLite (metadata only)

## Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with S3 bucket
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/filepad.git
cd filepad

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your AWS credentials

# Run migrations
python manage.py makemigrations filepad
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit http://localhost:8000

### Environment Variables

Create a `.env` file with:

```env
DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here

USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## AWS S3 Setup

1. **Create S3 Bucket**
   - Go to AWS Console → S3
   - Create bucket (e.g., `my-filepad-storage`)
   - Keep it private

2. **Create IAM User**
   - Go to IAM → Users → Create user
   - Attach policy with S3 access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}
```

3. **Get Credentials**
   - Create access key
   - Save Access Key ID and Secret Access Key
   - Add to `.env` file

## Production Deployment

### Using Gunicorn + Nginx

1. **Install on server:**
```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/filepad.git
cd filepad
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
nano .env  # Add your credentials
```

3. **Setup database:**
```bash
python3 manage.py migrate
```

4. **Create systemd service** (`/etc/systemd/system/filepad.service`):
```ini
[Unit]
Description=FilePad Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/filepad
EnvironmentFile=/var/www/filepad/.env
ExecStart=/var/www/filepad/venv/bin/gunicorn --workers 3 --bind unix:/var/www/filepad/filepad.sock filepad_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

5. **Enable and start:**
```bash
sudo systemctl enable filepad
sudo systemctl start filepad
```

6. **Configure Nginx** (example):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://unix:/var/www/filepad/filepad.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Usage

1. **Access FilePad** - Navigate to your domain
2. **Enter Password** - 4-32 characters (creates new space if first time)
3. **Upload Files** - Click upload area or drag & drop (max 10MB)
4. **Manage Files** - Download or delete your files
5. **Logout** - Click logout when done

## Security Features

- Password hashing with SHA-256
- Private S3 buckets with signed URLs
- CSRF protection
- No plain-text password storage
- User isolation (each password = separate space)

## File Structure

```
filepad/
├── filepad_project/       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── filepad/              # Main app
│   ├── models.py         # Database models
│   ├── views.py          # API endpoints
│   ├── serializers.py    # DRF serializers
│   └── urls.py           # App URLs
├── templates/
│   └── index.html        # Frontend
├── requirements.txt
├── .env.example
├── .gitignore
└── manage.py
```

## API Endpoints

- `POST /api/auth/` - Authenticate user
- `GET /api/files/` - List user's files
- `POST /api/upload/` - Upload file
- `DELETE /api/files/<id>/delete/` - Delete file
- `GET /api/files/<id>/download/` - Download file

## Development

```bash
# Run tests
python manage.py test

# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Troubleshooting

**S3 Connection Issues:**
- Verify AWS credentials in `.env`
- Check bucket name and region
- Ensure IAM user has correct permissions

**File Upload Fails:**
- Check file size (max 10MB)
- Verify S3 bucket exists
- Check server logs: `sudo journalctl -u filepad`

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Author

Your Name

## Acknowledgments

- Django Framework
- Django REST Framework
- django-storages
- AWS S3
