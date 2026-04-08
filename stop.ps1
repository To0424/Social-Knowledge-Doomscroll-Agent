#!/usr/bin/env pwsh
# Stop all SocialScope services.
# Usage:
#   .\stop.ps1           # stop and remove containers
#   .\stop.ps1 -Volumes  # also remove volumes (wipes DB data)

param(
    [switch]$Volumes
)

$files = @(
    "docker-compose.yml",
    "docker-compose.app.yml",
    "docker-compose.scheduler.yml"
)

$args = $files | ForEach-Object { "-f"; $_ }
$args += "--profile"; $args += "pgadmin"

if ($Volumes) {
    docker compose @args down -v
} else {
    docker compose @args down
}
