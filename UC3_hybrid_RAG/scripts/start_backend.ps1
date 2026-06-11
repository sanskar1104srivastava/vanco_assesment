param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipIngest,
    [switch]$SkipNeo4j,
    [switch]$SkipOllama,
    [switch]$ResetGraph
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvPath = Join-Path $ProjectRoot ".env"
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$LogsPath = Join-Path $ProjectRoot "logs"

Set-Location $ProjectRoot
New-Item -ItemType Directory -Force -Path $LogsPath | Out-Null

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtual environment not found at $Python. Run: python -m venv venv; venv\Scripts\python.exe -m pip install -r requirements.txt"
}

function Read-EnvMap {
    $map = @{}
    if (-not (Test-Path -LiteralPath $EnvPath)) {
        return $map
    }

    foreach ($line in Get-Content -LiteralPath $EnvPath) {
        if ($line.Trim() -eq "" -or $line.TrimStart().StartsWith("#")) {
            continue
        }
        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2) {
            $map[$parts[0].Trim()] = $parts[1]
        }
    }
    return $map
}

function Set-EnvValue {
    param(
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path -LiteralPath $EnvPath)) {
        New-Item -ItemType File -Path $EnvPath | Out-Null
    }

    $lines = @(Get-Content -LiteralPath $EnvPath -ErrorAction SilentlyContinue)
    $pattern = "^\s*$([regex]::Escape($Key))="
    $updated = $false
    $next = foreach ($line in $lines) {
        if ($line -match $pattern) {
            $updated = $true
            "$Key=$Value"
        } else {
            $line
        }
    }

    if (-not $updated) {
        $next += "$Key=$Value"
    }

    Set-Content -LiteralPath $EnvPath -Value $next -Encoding ascii
}

function Reload-Env {
    $script:EnvMap = Read-EnvMap
    foreach ($key in $script:EnvMap.Keys) {
        [Environment]::SetEnvironmentVariable($key, $script:EnvMap[$key], "Process")
    }
}

function Env-OrDefault {
    param(
        [string]$Key,
        [string]$Default
    )
    if ($script:EnvMap.ContainsKey($Key) -and $script:EnvMap[$Key].Trim() -ne "") {
        return $script:EnvMap[$Key]
    }
    return $Default
}

function Resolve-ProjectPath {
    param([string]$PathValue)
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }
    return Join-Path $ProjectRoot $PathValue
}

function Test-Neo4jConnectivity {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $Python (Join-Path $ProjectRoot "scripts\neo4j_probe.py") connect 2>&1
        $script:Neo4jLastError = ($output | Select-Object -Last 1)
        if ($LASTEXITCODE -eq 0) {
            $script:Neo4jLastError = ""
            return $true
        }
        return $false
    } catch {
        $script:Neo4jLastError = $_.Exception.Message
        return $false
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Wait-Neo4j {
    param([int]$TimeoutSeconds = 120)

    Write-Host "Waiting for Neo4j at $(Env-OrDefault 'NEO4J_URI' 'neo4j://localhost:7687') ..."
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Neo4jConnectivity) {
            Write-Host "Neo4j is ready."
            return
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 3
    }
    Write-Host ""
    throw "Neo4j did not become ready within $TimeoutSeconds seconds. Last connection error: $script:Neo4jLastError"
}

function Get-GraphNodeCount {
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $Python (Join-Path $ProjectRoot "scripts\neo4j_probe.py") count 2>&1
        if ($LASTEXITCODE -ne 0) {
            return -1
        }
        $count = $output | Where-Object { "$_".Trim() -match "^\d+$" } | Select-Object -Last 1
        if ($null -eq $count) {
            return -1
        }
        return [int]$count
    } catch {
        return -1
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

function Ensure-Neo4j {
    if ($SkipNeo4j) {
        Write-Host "Skipping Neo4j bootstrap."
        return
    }

    $uri = Env-OrDefault "NEO4J_URI" ""
    $username = Env-OrDefault "NEO4J_USERNAME" ""
    $password = Env-OrDefault "NEO4J_PASSWORD" ""
    $database = Env-OrDefault "NEO4J_DATABASE" "neo4j"

    if ($uri -eq "" -or $username -eq "" -or $password -eq "") {
        $docker = Get-Command docker -ErrorAction SilentlyContinue
        if (-not $docker) {
            throw "Neo4j credentials are missing and Docker is not available. Install Docker or set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env."
        }

        if ($uri -eq "") {
            Set-EnvValue "NEO4J_URI" "neo4j://localhost:7687"
        }
        if ($username -eq "") {
            Set-EnvValue "NEO4J_USERNAME" "neo4j"
        }
        if ($password -eq "") {
            $generatedPassword = "neo4j-" + ([guid]::NewGuid().ToString("N").Substring(0, 16))
            Set-EnvValue "NEO4J_PASSWORD" $generatedPassword
            Write-Host "Generated a local Neo4j password and saved it in .env."
        }
        if ($database -eq "") {
            Set-EnvValue "NEO4J_DATABASE" "neo4j"
        }
        Set-EnvValue "NEO4J_REQUIRED" "true"
        if (-not $script:EnvMap.ContainsKey("NEO4J_DOCKER_CONTAINER")) {
            Set-EnvValue "NEO4J_DOCKER_CONTAINER" "hybrid-rag-neo4j"
        }
        Reload-Env
    }

    $uri = Env-OrDefault "NEO4J_URI" ""
    $username = Env-OrDefault "NEO4J_USERNAME" "neo4j"
    $password = Env-OrDefault "NEO4J_PASSWORD" ""
    $container = Env-OrDefault "NEO4J_DOCKER_CONTAINER" "hybrid-rag-neo4j"
    $isLocal = $uri -match "localhost|127\.0\.0\.1|\[::1\]"

    if ($isLocal) {
        $docker = Get-Command docker -ErrorAction SilentlyContinue
        if ($docker) {
            $exists = docker ps -a --filter "name=^/$container$" --format "{{.Names}}"
            $running = docker ps --filter "name=^/$container$" --format "{{.Names}}"

            if (-not $exists) {
                Write-Host "Creating Neo4j Docker container '$container'."
                docker run --name $container -p 7474:7474 -p 7687:7687 -e "NEO4J_AUTH=$username/$password" -d neo4j:5 | Out-Host
            } elseif (-not $running) {
                Write-Host "Starting Neo4j Docker container '$container'."
                docker start $container | Out-Host
            } else {
                Write-Host "Neo4j Docker container '$container' is already running."
            }
        } else {
            Write-Host "Docker is not available; assuming local Neo4j is already running."
        }
    }

    Wait-Neo4j
}

function Test-OllamaApi {
    param([string]$BaseUrl)
    try {
        Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/api/tags" -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Ensure-Ollama {
    if ($SkipOllama) {
        Write-Host "Skipping Ollama check."
        return
    }

    $provider = (Env-OrDefault "LLM_PROVIDER" "ollama").ToLowerInvariant()
    if ($provider -ne "ollama") {
        Write-Host "LLM_PROVIDER=$provider; no Ollama bootstrap needed."
        return
    }

    $baseUrl = Env-OrDefault "OLLAMA_BASE_URL" "http://localhost:11434"
    $model = Env-OrDefault "OLLAMA_MODEL" "llama3.1"

    if (-not (Test-OllamaApi $baseUrl)) {
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        if (-not $ollama) {
            Write-Warning "Ollama is selected but the 'ollama' command was not found. Install/start Ollama or set LLM_PROVIDER=groq/extractive/openai/mistral/llama."
            return
        }

        Write-Host "Starting Ollama service."
        Start-Process -FilePath $ollama.Source -ArgumentList @("serve") -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogsPath "ollama.out.log") -RedirectStandardError (Join-Path $LogsPath "ollama.err.log")

        $deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt $deadline) {
            if (Test-OllamaApi $baseUrl) {
                break
            }
            Start-Sleep -Seconds 2
        }
    }

    if (-not (Test-OllamaApi $baseUrl)) {
        Write-Warning "Ollama did not respond at $baseUrl. Backend can start, but /ask will fail until the LLM is available."
        return
    }

    $tags = Invoke-RestMethod -Uri "$($baseUrl.TrimEnd('/'))/api/tags" -TimeoutSec 10
    $installed = @($tags.models | ForEach-Object { $_.name })
    $modelFound = $false
    foreach ($name in $installed) {
        if ($name -eq $model -or $name -like "$model`:*") {
            $modelFound = $true
        }
    }

    if (-not $modelFound) {
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        if ($ollama) {
            Write-Host "Pulling Ollama model '$model'."
            & $ollama.Source pull $model
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to pull Ollama model '$model'."
            }
        } else {
            Write-Warning "Ollama model '$model' is not installed."
        }
    } else {
        Write-Host "Ollama model '$model' is available."
    }
}

function Test-ChunkConfigMatches {
    param([string]$ChunksPath)

    if (-not (Test-Path -LiteralPath $ChunksPath)) {
        return $false
    }

    try {
        $chunks = Get-Content -LiteralPath $ChunksPath -Raw | ConvertFrom-Json
        if ($null -eq $chunks -or $chunks.Count -eq 0) {
            return $false
        }

        $expectedChunkSize = [int](Env-OrDefault "CHUNK_SIZE" "350")
        $expectedChunkOverlap = [int](Env-OrDefault "CHUNK_OVERLAP" "100")
        $sample = $chunks | Select-Object -First 1
        $metadata = $sample.metadata

        if ($null -eq $metadata.chunk_size -or $null -eq $metadata.chunk_overlap) {
            return $false
        }

        return ([int]$metadata.chunk_size -eq $expectedChunkSize -and [int]$metadata.chunk_overlap -eq $expectedChunkOverlap)
    } catch {
        return $false
    }
}

function Ensure-Ingestion {
    if ($SkipIngest) {
        Write-Host "Skipping ingestion check."
        return
    }

    $pdfPath = Resolve-ProjectPath (Env-OrDefault "PDF_PATH" "data/physics.pdf")
    if (-not (Test-Path -LiteralPath $pdfPath)) {
        throw "PDF not found at $pdfPath. Place the NCERT PDF there or set PDF_PATH in .env."
    }

    $chunksPath = Resolve-ProjectPath (Env-OrDefault "CHUNKS_PATH" "data/chunks.json")
    $bm25Path = Resolve-ProjectPath (Env-OrDefault "BM25_INDEX_PATH" "data/bm25_index.pkl")
    $graphCount = 0
    $chunkConfigMatches = Test-ChunkConfigMatches $chunksPath

    if (-not $SkipNeo4j) {
        $graphCount = Get-GraphNodeCount
    }

    $needsIngest = $ResetGraph -or
        (-not (Test-Path -LiteralPath $chunksPath)) -or
        (-not (Test-Path -LiteralPath $bm25Path)) -or
        (-not $chunkConfigMatches) -or
        (-not $SkipNeo4j -and $graphCount -le 0)

    if ($needsIngest) {
        Write-Host "Running ingestion before backend startup."
        $args = @("-m", "backend.ingest", "--pdf", $pdfPath)
        if ($ResetGraph -or (-not $chunkConfigMatches) -or (-not $SkipNeo4j -and $graphCount -le 0)) {
            $args += "--reset-graph"
        }
        & $Python @args
        if ($LASTEXITCODE -ne 0) {
            throw "Ingestion failed."
        }
    } else {
        Write-Host "Indexes and Neo4j graph look ready; skipping ingestion."
    }
}

Reload-Env
Ensure-Neo4j
Reload-Env
Ensure-Ollama
Ensure-Ingestion

Write-Host "Starting FastAPI at http://$HostName`:$Port"
& $Python -m uvicorn backend.api:app --host $HostName --port $Port
