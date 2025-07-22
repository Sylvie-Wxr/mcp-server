# MCP Server

A FastAPI-based MCP (Model Context Protocol) server with addition and string reversal endpoints.

## Features

- ✅ FastAPI web server with auto-generated OpenAPI docs
- ✅ Addition endpoint for mathematical operations
- ✅ String reversal endpoint
- ✅ MCP manifest endpoint for service discovery
- ✅ Docker containerization
- ✅ Nginx reverse proxy configuration
- ✅ Automated EC2 deployment
- ✅ GitHub Actions CI/CD pipeline

## API Endpoints

- `GET /mcp/manifest` - Service discovery endpoint
- `POST /add` - Add two numbers
- `POST /reverse` - Reverse a string

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional, for containerized development)

### Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the development server:
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
   ```

3. Access the API:
   - API: http://localhost:3001
   - Interactive docs: http://localhost:3001/docs
   - Manifest: http://localhost:3001/mcp/manifest

### Docker Development

1. Build the image:
   ```bash
   docker build -t mcp-server .
   ```

2. Run the container:
   ```bash
   docker run -p 3001:3001 mcp-server
   ```

3. Or use Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Deployment

### 1. GitHub Setup

1. Create a new repository on GitHub
2. Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/mcp-server.git
   git push -u origin main
   ```

### 2. EC2 Instance Setup

1. Launch an Ubuntu 22.04 EC2 instance
2. Configure security groups:
   - SSH (22) - Your IP only
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0 (optional, for SSL)

3. SSH into your instance and run the deployment script:
   ```bash
   # Copy the deploy script to your EC2 instance
   wget https://raw.githubusercontent.com/YOUR_USERNAME/mcp-server/main/deploy/deploy.sh
   chmod +x deploy.sh
   
   # Edit the script to update the REPO_URL with your GitHub repository
   nano deploy.sh
   
   # Run the deployment
   ./deploy.sh
   ```

### 3. Nginx Configuration

The deployment script automatically configures Nginx, but you may need to:

1. Update the domain name in `/etc/nginx/sites-available/mcp-server.conf`
2. Restart Nginx: `sudo systemctl restart nginx`

### 4. GitHub Actions (Optional)

For automated deployments:

1. Copy `deploy/github-actions.yml` to `.github/workflows/deploy.yml` in your repository

2. Add the following secrets to your GitHub repository:
   - `EC2_HOST`: Your EC2 instance public IP
   - `EC2_USERNAME`: `ubuntu` (or your EC2 username)
   - `EC2_SSH_KEY`: Your private SSH key content

3. Push to the main branch to trigger automatic deployment

### 5. SSL Certificate (Optional)

To enable HTTPS:

1. Install Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. Get SSL certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. Uncomment the SSL configuration in `/etc/nginx/sites-available/mcp-server.conf`

## Usage Examples

### Add Numbers
```bash
curl -X POST "http://your-domain.com/add" \
     -H "Content-Type: application/json" \
     -d '{"a": 5, "b": 3}'
```

### Reverse String
```bash
curl -X POST "http://your-domain.com/reverse" \
     -H "Content-Type: application/json" \
     -d '{"text": "hello world"}'
```

### Get Manifest
```bash
curl "http://your-domain.com/mcp/manifest"
```

## File Structure

```
mcp-server/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── deploy/
│   ├── deploy.sh           # EC2 deployment script
│   └── github-actions.yml  # GitHub Actions workflow
├── nginx/
│   └── mcp-server.conf     # Nginx configuration
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # Python dependencies
├── README.md
└── uv.lock
```

## Monitoring

- Check application status: `docker ps`
- View application logs: `docker logs mcp-server`
- Check Nginx status: `sudo systemctl status nginx`
- View Nginx logs: `sudo tail -f /var/log/nginx/error.log`

## Troubleshooting

### Application won't start
- Check Docker logs: `docker logs mcp-server`
- Verify port 3001 is available: `sudo netstat -tlnp | grep 3001`

### Nginx issues
- Test configuration: `sudo nginx -t`
- Check logs: `sudo tail -f /var/log/nginx/error.log`
- Restart service: `sudo systemctl restart nginx`

### Firewall issues
- Check UFW status: `sudo ufw status`
- Allow HTTP/HTTPS: `sudo ufw allow 'Nginx Full'`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (when available)
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).