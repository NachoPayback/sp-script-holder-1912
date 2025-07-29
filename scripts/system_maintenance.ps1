# Creates visual desktop effects and system notifications

param(
    [string]$Effect = "random"
)

function Show-SystemOptimizer {
    Write-Host "Starting system optimization..." -ForegroundColor Green
    for ($i = 0; $i -le 100; $i += 10) {
        Write-Progress -Activity "Optimizing System" -Status "Progress: $i%" -PercentComplete $i
        Start-Sleep -Milliseconds 200
    }
    Write-Progress -Activity "Optimizing System" -Completed
    Write-Host "System optimization complete!" -ForegroundColor Yellow
}

function Show-SystemUpdater {
    Write-Host "Installing important updates..." -ForegroundColor Cyan
    $apps = @("Critical Security Update", "Driver Update", "System Patch", "Windows Update")
    
    foreach ($app in $apps) {
        Write-Host "Installing: $app" -ForegroundColor White
        Start-Sleep -Seconds 1
    }
    Write-Host "All updates installed successfully!" -ForegroundColor Green
}

function Show-SystemNotification {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        "System notification: Process completed successfully.",
        "System Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
}

# Main execution
try {
    switch ($Effect) {
        "loader" { Show-SystemOptimizer }
        "installer" { Show-SystemUpdater }
        "error" { Show-SystemNotification }
        default { 
            $effects = @("loader", "installer", "error")
            $randomEffect = Get-Random -InputObject $effects
            & $PSCommandPath -Effect $randomEffect
        }
    }
    
    Write-Host "Process executed successfully!" -ForegroundColor Magenta
    exit 0
    
} catch {
    Write-Host "Error executing process: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 