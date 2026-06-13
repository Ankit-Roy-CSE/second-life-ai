# =============================================================================
# dev.ps1 — Local stack helper for Amazon Second Life AI (PowerShell)
# =============================================================================
# Usage:
#   .\scripts\dev.ps1 up          # build + start full stack
#   .\scripts\dev.ps1 up infra    # start infra only
#   .\scripts\dev.ps1 down        # stop all containers
#   .\scripts\dev.ps1 reset       # stop + wipe all volumes
#   .\scripts\dev.ps1 logs        # tail all service logs
#   .\scripts\dev.ps1 ps          # show container status
# =============================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(Position=1)]
    [string]$SubCommand = ""
)

$ErrorActionPreference = "Stop"
$INFRA = "postgres", "redis", "minio", "minio-init"

function Ensure-Env {
    if (-not (Test-Path ".env")) {
        Write-Host "⚠ .env not found — copying .env.example"
        Copy-Item ".env.example" ".env"
    }
}

switch ($Command) {
    "up" {
        if ($SubCommand -eq "infra") {
            Write-Host "▶ Starting infra services..."
            docker compose up --build -d @INFRA
        } else {
            Ensure-Env
            Write-Host "▶ Starting full stack..."
            docker compose up --build -d
        }
        Write-Host "✅ Stack is up."
        docker compose ps
    }
    "down" {
        Write-Host "▶ Stopping containers..."
        docker compose down
    }
    "reset" {
        Write-Host "⚠ Wiping all volumes..."
        docker compose down -v
        Write-Host "✅ Volumes wiped."
    }
    "logs" {
        docker compose logs -f
    }
    "ps" {
        docker compose ps
    }
    default {
        Write-Host "Usage: .\scripts\dev.ps1 {up [infra]|down|reset|logs|ps}"
        exit 1
    }
}
