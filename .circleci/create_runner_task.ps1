# Define the path to your script
$scriptPath = $PSScriptRoot + "\Start-CircleCIRunner.ps1"

# Task name and description
$taskName = "CircleCI Runner Agent"
$taskDescription = "Automatically runs the CircleCI Runner Agent at startup."

# Get the current user
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Check if the task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

# If the task exists, remove it
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing the existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false

    # Wait a moment to ensure the task is fully removed
    Start-Sleep -Seconds 2
}

# Create a new action to run the script with PowerShell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""

# Create a trigger to start the task at system startup
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create a new principal to run the task under the current user account with the highest privileges
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Highest

# Create the scheduled task settings (run only if idle, allow start on batteries)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries

# Create the scheduled task
Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings -TaskName $taskName -Description $taskDescription

Write-Host "Scheduled task '$taskName' has been created successfully!"

# Run the task immediately
Write-Host "Starting the task immediately..."
Start-ScheduledTask -TaskName $taskName

Write-Host "Task '$taskName' started successfully!"
