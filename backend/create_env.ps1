# PowerShell script to create .env file
$envContent = @"
# Backend Configuration
DATABASE_URL=mysql+asyncmy://root:gjl421911@localhost:3306/xqfc_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-very-secure-secret-key-here-change-in-production
DEBUG=false

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=County Real Estate Platform
VERSION=0.1.0
DESCRIPTION=County Real Estate Information Platform API

# Security Settings
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_MINUTES=20160

# CORS
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:8080", "https://xqfc.com"]

# File Storage
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
STATIC_DIR=./static

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
"@

$envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
Write-Host ".env file created successfully!"
