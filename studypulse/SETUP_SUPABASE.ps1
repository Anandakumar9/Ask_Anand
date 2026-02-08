# ===================================================================
# StudyPulse - Setup Supabase Database
# ===================================================================
# This script helps you set up the Supabase database
# Run this ONCE before using the app for the first time
# ===================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  StudyPulse - Supabase Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will guide you through setting up your Supabase database." -ForegroundColor Yellow
Write-Host ""

# Read SQL file
$sqlFile = "$PSScriptRoot\backend\supabase_schema.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "ERROR: SQL file not found: $sqlFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Open Supabase Dashboard" -ForegroundColor Green
Write-Host "  Opening browser..." -ForegroundColor White
Start-Process "https://app.supabase.com/project/eguewniqweyrituwbowt/editor"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Step 2: Navigate to SQL Editor" -ForegroundColor Green
Write-Host "  1. In Supabase, click 'SQL Editor' in the left menu" -ForegroundColor White
Write-Host "  2. Click 'New Query'" -ForegroundColor White

Write-Host ""
Write-Host "Step 3: Copy SQL Schema" -ForegroundColor Green
Write-Host "  The SQL file will be copied to your clipboard..." -ForegroundColor White
Get-Content $sqlFile | Set-Clipboard
Write-Host "  ✓ SQL copied to clipboard!" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Paste and Run" -ForegroundColor Green
Write-Host "  1. Paste (Ctrl+V) in the SQL Editor" -ForegroundColor White
Write-Host "  2. Click 'Run' button" -ForegroundColor White
Write-Host "  3. Wait for 'Success' message" -ForegroundColor White

Write-Host ""
Write-Host "Step 5: Verify Tables Created" -ForegroundColor Green
Write-Host "  1. Click 'Table Editor' in left menu" -ForegroundColor White
Write-Host "  2. You should see tables: users, exams, subjects, topics, etc." -ForegroundColor White

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Instructions Displayed" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "After completing steps above, you're ready to use StudyPulse!" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter after you've completed the setup"

Write-Host ""
Write-Host "Testing connection to Supabase..." -ForegroundColor Yellow

# Test Supabase connection
cd "$PSScriptRoot\backend"
python -c "import asyncio; from app.core.supabase import supabase_client; asyncio.run(supabase_client.test_connection())" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Supabase connection successful!" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Could not verify connection. Please check your setup." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
