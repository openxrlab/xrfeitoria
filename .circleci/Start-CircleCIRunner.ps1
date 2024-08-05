$installDirPath = "D:\Program Files\CircleCI"
$agentPath = Join-Path -Path $installDirPath -ChildPath "circleci-runner.exe"
$configPath = Join-Path -Path $installDirPath -ChildPath "runner-agent-config.yaml"

echo "Constantly running CircleCI Runner Agent"
while ($true) {
    echo "--- Restarting CircleCI Runner Agent ---"
    try {
        & $agentPath machine --config $configPath
    } catch {
        echo "Error: $_"
    }
    Start-Sleep 1
}
