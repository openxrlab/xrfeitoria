$installDirPath = "$env:ProgramFiles\CircleCI"
$agentFile = "circleci-runner.exe"
$cmd = "`"$installDirPath\$agentFile`" machine --config `"$installDirPath\runner-agent-config.yaml`""

echo "Constantly running command: $cmd"
while ($true) {
    Invoke-Expression $cmd
    Start-Sleep 1
}
