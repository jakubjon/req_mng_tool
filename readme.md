# Deployment Guide

## Quick Start (Local Development)

1. **Clone and navigate to the project:**
```bash
cd req_mng_tool
```

2. **Start the application:**
```bash
docker-compose up --build
```

3. **Access the application:**
- Main app: http://localhost:5000
- Directus CMS: http://localhost:8055 (admin@example.com / admin123)

4. **Stop the application:**
```bash
docker-compose down
```

## Production Deployment

### 1. Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://directus:directus@postgres:5432/directus

# Directus Configuration
DIRECTUS_URL=http://directus:8055
DIRECTUS_TOKEN=your_directus_token_here

# Flask Configuration
SECRET_KEY=your_secure_secret_key_here
FLASK_ENV=production

# Optional: Custom ports
FLASK_PORT=5000
DIRECTUS_PORT=8055
POSTGRES_PORT=5432
```

### 2. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  # Flask Application
  flask-app:
    build: .
    ports:
      - "80:5000"  # Expose on port 80
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - DIRECTUS_URL=${DIRECTUS_URL}
      - DIRECTUS_TOKEN=${DIRECTUS_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - directus
      - db-init
    networks:
      - req-mng-network
    restart: unless-stopped

  # Database initialization
  db-init:
    build: .
    command: python init_db.py
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
    networks:
      - req-mng-network

  # Directus CMS
  directus:
    image: directus/directus:latest
    ports:
      - "8055:8055"
    environment:
      - KEY=255d861b-5ea1-5996-9aa3-922530ec40b1
      - SECRET=6116487b-cda1-52c2-b5b5-c8022c45e263
      - DB_CLIENT=pg
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_DATABASE=directus
      - DB_USER=directus
      - DB_PASSWORD=directus
      - ADMIN_EMAIL=admin@example.com
      - ADMIN_PASSWORD=admin123
      - CORS_ENABLED=true
      - CORS_ORIGIN=http://localhost:5000
    depends_on:
      - postgres
    networks:
      - req-mng-network
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=directus
      - POSTGRES_USER=directus
      - POSTGRES_PASSWORD=directus
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - req-mng-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  req-mng-network:
    driver: bridge
```

### 3. Deploy to Production

```bash
# Start production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production deployment
docker-compose -f docker-compose.prod.yml down
```

## Cloud Deployment Options

### AWS Deployment

1. **EC2 Instance:**
```bash
# Install Docker on EC2
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone <your-repo>
cd req_mng_tool
docker-compose up -d
```

2. **AWS ECS (Elastic Container Service):**
- Create ECS cluster
- Define task definitions for each service
- Set up Application Load Balancer
- Configure environment variables

### Google Cloud Platform

1. **Google Compute Engine:**
```bash
# Similar to AWS EC2 setup
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

2. **Google Cloud Run:**
- Build and push Docker images to Container Registry
- Deploy each service separately
- Set up Cloud SQL for PostgreSQL

### Azure Deployment

1. **Azure Container Instances:**
```bash
# Deploy using Azure CLI
az container create --resource-group myResourceGroup --name req-mng-app --image your-registry.azurecr.io/flask-app:latest
```

2. **Azure Kubernetes Service (AKS):**
- Create AKS cluster
- Deploy using Kubernetes manifests
- Set up Azure Database for PostgreSQL

## Monitoring and Maintenance

### Health Checks

The application includes health check endpoints:
- Flask app: `GET /api/health`
- Docker health checks configured in Dockerfile

### Logs

```bash
# View application logs
docker-compose logs flask-app

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs directus
```

### Database Backup

```bash
# Backup PostgreSQL data
docker-compose exec postgres pg_dump -U directus directus > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U directus directus < backup.sql
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Change ports in docker-compose.yml
   - Check if ports 5000, 8055, 5432 are available

2. **Database connection issues:**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL environment variable
   - Verify network connectivity

3. **Permission issues:**
   - Ensure uploads directory has proper permissions
   - Check Docker user permissions

4. **Memory issues:**
   - Increase Docker memory allocation
   - Monitor resource usage

### Debug Mode

```bash
# Run with debug output
docker-compose up --build --verbose

# Access container shell
docker-compose exec flask-app bash
```

## Security Considerations

1. **Change default passwords:**
   - Update Directus admin password
   - Use strong SECRET_KEY
   - Change database passwords

2. **Network security:**
   - Use reverse proxy (nginx)
   - Enable HTTPS
   - Configure firewall rules

3. **Data protection:**
   - Regular backups
   - Encrypt sensitive data
   - Monitor access logs 