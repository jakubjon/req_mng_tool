# Railway Deployment

This directory contains the Docker Compose configuration used to deploy the Requirements Management Tool on [Railway](https://railway.app/).

The compose file builds the Flask application from the project root and starts a PostgreSQL service. When creating a Railway project, select **Deploy from Repository** and set this folder (`railway/`) as the service root. Railway will automatically build and run both containers.

```bash
# Deploy using the Railway CLI
railway up
```

Environment variables for database credentials can be configured in the Railway dashboard. The defaults are already defined in the compose file and match the local development setup.
