# Define the Python script to run
$pythonScript = "main.py"

# Define the Python commands to try
$pythonCommands = @("python", "py", "python3")

# Loop through each Python command
foreach ($command in $pythonCommands) {
    try {
        # Check if the command is available
        $commandPath = Get-Command $command -ErrorAction Stop | Select-Object -ExpandProperty Source

        # If the command is available, try to run the script
        Write-Host "Trying to run the script with $command..."
        & $command $pythonScript
        break  # Exit the loop if the script runs successfully
    }
    catch {
        # If the command is not available, continue to the next one
        Write-Host "$command is not available, trying the next command..."
    }
}