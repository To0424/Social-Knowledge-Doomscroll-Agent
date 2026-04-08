#!/usr/bin/env pwsh
# Start the full SocialScope stack (infra + app + scheduler).
# Usage:
#   .\start.ps1              # CPU (default)
#   .\start.ps1 -GPU         # with NVIDIA GPU for Ollama
#   .\start.ps1 -PgAdmin     # include pgAdmin
#   .\start.ps1 -GPU -PgAdmin

param(
    [switch]$GPU
)

$files = @(
    "docker-compose.yml",
    "docker-compose.app.yml",
    "docker-compose.scheduler.yml"
)

if ($GPU) { $files += "docker-compose.gpu.yml" }

$args = $files | ForEach-Object { "-f"; $_ }
$args += "--profile"; $args += "pgadmin"

docker compose @args up --build -d
