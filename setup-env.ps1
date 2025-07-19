# Environment Variables for Local Development
$env:DATABASE_URL="postgresql://reqmng:reqmng@localhost:5432/reqmng"
$env:FLASK_ENV="development"
$env:FLASK_DEBUG="1"
$env:SECRET_KEY="dev-secret-key-change-in-production"

Write-Host "Environment variables set for local development"
Write-Host "DATABASE_URL: $env:DATABASE_URL"
Write-Host "FLASK_ENV: $env:FLASK_ENV"
