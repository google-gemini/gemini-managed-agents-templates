param(
    [string]$Prompt = ""
)

if (-not $env:GEMINI_API_KEY) {
    Write-Host "Error: GEMINI_API_KEY is not set in your environment." -ForegroundColor Red
    Write-Host "Set it by running: `$env:GEMINI_API_KEY = 'your_gemini_api_key'" -ForegroundColor Yellow
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    $Prompt = python -c "import yaml; print(yaml.safe_load(open('agent.yaml'))['examples'][0]['prompt'])"
}

Write-Host "Starting Shopping Agent with query: $Prompt" -ForegroundColor Cyan

python ..\generate_payload.py "$Prompt" > probers.json

curl.exe -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" `
  -H "Content-Type: application/json" `
  -H "Accept: text/event-stream" `
  -H "x-goog-api-key: $env:GEMINI_API_KEY" `
  -H "Api-Revision: 2026-05-20" `
  -H "x-server-timeout: 600" `
  -d "@probers.json" | Tee-Object -FilePath prober_output.log

Remove-Item -Path probers.json -ErrorAction SilentlyContinue
