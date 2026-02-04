# Repo_Analysis_Rag_Agent Local CI/CD Pipeline Script
# Simulates GitHub Actions CI/CD pipeline locally for Windows PowerShell
# Usage: .\run-local-cicd.ps1

param(
    [string]$Stage = 'all',
    [switch]$SkipTests,
    [switch]$SkipDocker,
    [switch]$Verbose,
    [switch]$Python,
    [switch]$TypeScript,
    [switch]$Unit,
    [switch]$Functional,
    [switch]$Integration,
    [switch]$E2E
)

$ErrorActionPreference = "Stop"
if ($Verbose) {
    $VerbosePreference = "Continue"
} else {
    $VerbosePreference = "SilentlyContinue"
}

$testFilterSpecified = $Python -or $TypeScript -or $Unit -or $Functional -or $Integration -or $E2E
if ($testFilterSpecified -and $Stage -eq 'all') {
    $Stage = 'test'
}

# Ensure we run from repo root so linting, tests, Docker, and compose paths resolve correctly
Set-Location $PSScriptRoot

# Repo-specific paths (no src/ at root)
$PythonPaths = @("repo_analysis_rag/", "offline-folder-rag/edge_agent/", "tests/")
$PythonPathsStr = $PythonPaths -join ", "

function Write-Success {
    param([string]$Message)
    Write-Host "SUCCESS: $Message"
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "ERROR: $Message"
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "WARNING: $Message"
}

function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message"
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n========================================"
    Write-Host "$Title"
    Write-Host "========================================`n"
}

# Stage 1: Setup Environment
function Invoke-Setup {
    Write-Section "STAGE 1: Setup Environment"

    Write-Info "Checking Python installation..."
    $pythonVersion = python --version 2>&1
    if ($?) {
        Write-Success "Python found: $pythonVersion"
    } else {
        Write-Error-Message "Python not found. Please install Python 3.11+"
        exit 1
    }

    Write-Info "Checking pip..."
    pip --version | Out-Null
    if ($?) {
        Write-Success "pip is available"
    } else {
        Write-Error-Message "pip not found"
        exit 1
    }

    Write-Info "Checking Docker..."
    docker --version | Out-Null
    if ($?) {
        Write-Success "Docker is installed"
    } else {
        Write-Warning-Message "Docker not found. Docker build will be skipped."
    }

    Write-Info "Creating virtual environment if needed..."
    if (-not (Test-Path ".venv") -or -not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
        if (Test-Path ".venv") {
            Write-Warning-Message "Virtual environment exists but activation script is missing. Using existing environment."
            Write-Success "Virtual environment ready (with limitations)"
        } else {
            python -m venv .venv
            Write-Success "Virtual environment created"
        }
    } else {
        Write-Success "Virtual environment already exists"
    }

    Write-Info "Setting up virtual environment..."
    if (Test-Path ".\.venv\Scripts\python.exe") {
        $venvPath = Resolve-Path ".\.venv\Scripts"
        $env:PATH = "$venvPath;$env:PATH"
        Write-Success "Virtual environment configured"
    } else {
        Write-Warning-Message "Virtual environment Python not found - using system Python"
    }

    Write-Info "Ensuring pip is available in virtual environment..."
    if (Test-Path ".\.venv\Scripts\python.exe") {
        try {
            & ".\.venv\Scripts\python.exe" -c "import pip" 2>$null
        } catch {
            Write-Info "Bootstrapping pip in virtual environment..."
            & ".\.venv\Scripts\python.exe" -m ensurepip --upgrade 2>$null
        }

        & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
        if ($?) {
            Write-Success "Pip and tools upgraded in virtual environment"
        } else {
            Write-Warning-Message "Failed to upgrade pip in virtual environment"
        }

        Write-Info "Installing project dependencies..."
        if (Test-Path "requirements.txt") {
            & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
            if ($?) { Write-Success "Project dependencies installed" } else { Write-Warning-Message "Failed to install some project dependencies" }
        } else {
            Write-Warning-Message "requirements.txt not found - dependencies may be missing"
        }
        if (Test-Path "confluence_requirements.txt") {
            & ".\.venv\Scripts\python.exe" -m pip install -r confluence_requirements.txt
            if ($?) { Write-Success "Confluence dependencies installed" } else { Write-Warning-Message "Failed to install some confluence dependencies" }
        }
        if (Test-Path "offline-folder-rag\requirements.txt") {
            & ".\.venv\Scripts\python.exe" -m pip install -r offline-folder-rag\requirements.txt
            if ($?) { Write-Success "Offline-folder-rag dependencies installed" } else { Write-Warning-Message "Failed to install some offline-folder-rag dependencies" }
        }
    } else {
        python -m pip install --upgrade pip setuptools wheel
        Write-Success "Pip and tools upgraded (system Python)"
        if (Test-Path "requirements.txt") {
            pip install -r requirements.txt
            if ($?) { Write-Success "Project dependencies installed" } else { Write-Warning-Message "Failed to install some project dependencies" }
        } else {
            Write-Warning-Message "requirements.txt not found - dependencies may be missing"
        }
        if (Test-Path "confluence_requirements.txt") {
            pip install -r confluence_requirements.txt
            if ($?) { Write-Success "Confluence dependencies installed" } else { Write-Warning-Message "Failed to install some confluence dependencies" }
        }
        if (Test-Path "offline-folder-rag\requirements.txt") {
            pip install -r offline-folder-rag\requirements.txt
            if ($?) { Write-Success "Offline-folder-rag dependencies installed" } else { Write-Warning-Message "Failed to install some offline-folder-rag dependencies" }
        }
    }

    Write-Success "Setup completed"
}

# Stage 2: Linting
function Invoke-Lint {
    Write-Section "STAGE 2: Code Quality Checks (Linting)"

    $root = (Get-Location).Path
    $env:PYTHONPATH = "$root;$root\offline-folder-rag\edge_agent"

    Write-Info "Ensuring linting tools are installed..."
    pip install black ruff mypy pylint flake8 -q

    Write-Info "Running Black formatter check on $PythonPathsStr..."
    try {
        $blackProcess = Start-Process -FilePath "black" -ArgumentList "--check", "--diff", "repo_analysis_rag/", "offline-folder-rag/edge_agent/", "tests/" -NoNewWindow -Wait -PassThru
        $blackExitCode = $blackProcess.ExitCode
    } catch {
        $blackExitCode = 999
    }

    if ($blackExitCode -eq 0) {
        Write-Success "Black check passed - all files properly formatted"
    } elseif ($blackExitCode -eq 1) {
        Write-Warning-Message "Black found files that need formatting"
    } else {
        Write-Error-Message "Black failed with error (exit code: $blackExitCode)"
    }

    Write-Info "Running Ruff linter..."
    try {
        $ruffProcess = Start-Process -FilePath "ruff" -ArgumentList "check", "repo_analysis_rag/", "offline-folder-rag/edge_agent/", "tests/" -NoNewWindow -Wait -PassThru
        $ruffExitCode = $ruffProcess.ExitCode
    } catch {
        $ruffExitCode = 999
    }

    if ($ruffExitCode -eq 0) {
        Write-Success "Ruff check passed - no issues found"
    } else {
        Write-Warning-Message "Ruff found linting issues"
    }

    Write-Info "Running MyPy type checker..."
    try {
        & mypy repo_analysis_rag offline-folder-rag/edge_agent --ignore-missing-imports 2>$null
        $mypyExitCode = $LASTEXITCODE
    } catch {
        $mypyExitCode = 999
    }

    if ($mypyExitCode -eq 0) {
        Write-Success "MyPy check passed - no type issues found"
    } else {
        Write-Warning-Message "MyPy found type checking issues"
    }

    Write-Info "Running Pylint..."
    try {
        $pylintProcess = Start-Process -FilePath "pylint" -ArgumentList "repo_analysis_rag/", "offline-folder-rag/edge_agent/", "--disable=all", "--enable=E,F" -NoNewWindow -Wait -PassThru
        $pylintExitCode = $pylintProcess.ExitCode
    } catch {
        $pylintExitCode = 999
    }

    if ($pylintExitCode -eq 0) {
        Write-Success "Pylint check passed - no critical issues found"
    } else {
        Write-Warning-Message "Pylint found code quality issues"
    }

    Write-Info "Running Flake8..."
    try {
        $flake8Process = Start-Process -FilePath "flake8" -ArgumentList "repo_analysis_rag/", "offline-folder-rag/edge_agent/", "tests/", "--max-line-length=88", "--extend-ignore=E203,W503" -NoNewWindow -Wait -PassThru
        $flake8ExitCode = $flake8Process.ExitCode
    } catch {
        $flake8ExitCode = 999
    }

    if ($flake8ExitCode -eq 0) {
        Write-Success "Flake8 check passed - no style issues found"
    } else {
        Write-Warning-Message "Flake8 found style violations"
    }

    Write-Success "Linting stage completed"
}

# Stage 3: Security Checks
function Invoke-Security {
    Write-Section "STAGE 3: Security Checks"

    Write-Info "Installing security tools..."
    pip install bandit safety -q

    Write-Info "Running Bandit security scan on repo_analysis_rag and edge_agent..."
    try {
        $banditProcess = Start-Process -FilePath "bandit" -ArgumentList "-r", "repo_analysis_rag/", "offline-folder-rag/edge_agent/", "-f", "json", "-o", "bandit-report.json" -NoNewWindow -Wait -PassThru
        $banditExitCode = $banditProcess.ExitCode
    } catch {
        $banditExitCode = 999
    }

    if ($banditExitCode -eq 0) {
        Write-Success "Bandit scan completed (report: bandit-report.json)"
    } else {
        Write-Warning-Message "Bandit scan completed with issues (exit code: $banditExitCode)"
    }

    Write-Success "Security stage completed"
}

# Stage 4: Tests
function Invoke-Tests {
    Write-Section "STAGE 4: Unit, Functional, Integration, and E2E Tests"

    if ($SkipTests) {
        Write-Warning-Message 'Tests skipped (SkipTests flag)'
        return
    }

    Write-Info "Installing test dependencies..."
    $pythonExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
    & $pythonExe -m pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist -q
    & $pythonExe -m pip install -r requirements.txt -q 2>$null
    if (-not $?) { & $pythonExe -m pip install fastapi "uvicorn[standard]" httpx -q }

    Write-Info "Starting PostgreSQL/Redis services (Docker) for integration tests..."
    $dockerAvailable = $false
    try {
        docker version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $dockerAvailable = $true }
    } catch {
        $dockerAvailable = $false
    }

    if ($dockerAvailable) {
        $dockerCompose = @'
services:
  postgres-ide:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: zeroui_ide_user
      POSTGRES_PASSWORD: change_me_ide
      POSTGRES_DB: zeroui_ide_pg
    ports:
      - "5436:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zeroui_ide_user"]
      interval: 5s
      timeout: 3s
      retries: 20
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20
'@
        if (!(Test-Path "docker-compose.test.yml")) {
            $dockerCompose | Out-File "docker-compose.test.yml" -Encoding UTF8
        }
        try {
            $upProcess = Start-Process -FilePath "docker" -ArgumentList "compose", "-f", "docker-compose.test.yml", "up", "-d" -NoNewWindow -Wait -PassThru
            if ($upProcess.ExitCode -eq 0) {
                Write-Info "Waiting for services to be ready..."
                Start-Sleep -Seconds 5
                Write-Success "Docker services started successfully"
            } else {
                Write-Warning-Message "Docker services failed to start. Tests will run without database integration."
            }
        } catch {
            Write-Warning-Message "Docker services failed to start. Tests will run without database integration."
        }
    } else {
        Write-Warning-Message "Docker not available. Tests will run without database integration."
    }

    $runPython = $Python -or (-not $Python -and -not $TypeScript)
    $runTypeScript = $TypeScript -or (-not $Python -and -not $TypeScript)
    $runUnit = $Unit -or (-not $Unit -and -not $Functional -and -not $Integration -and -not $E2E)
    $runFunctional = $Functional -or (-not $Unit -and -not $Functional -and -not $Integration -and -not $E2E)
    $runIntegration = $Integration -or (-not $Unit -and -not $Functional -and -not $Integration -and -not $E2E)
    $runE2E = $E2E -or (-not $Unit -and -not $Functional -and -not $Integration -and -not $E2E)

    # PYTHONPATH so edge_agent and repo_analysis_rag are importable (use script dir as repo root)
    $repoRoot = $PSScriptRoot
    $env:PYTHONPATH = "$repoRoot;$repoRoot\offline-folder-rag"

    if ($runPython) {
        if ($runUnit) {
            Write-Info "Running Python unit tests (tests/confluence, tests/edge_agent/unit)..."
            & $pythonExe -m pytest "$repoRoot\tests\confluence" "$repoRoot\tests\edge_agent\unit" `
                --junitxml="$repoRoot\test-results-unit.xml" `
                -v --tb=short 2>$null
            if ($?) { Write-Success "Python unit tests completed" } else { Write-Warning-Message "Python unit tests failed or skipped" }
        }

        if ($runFunctional) {
            Write-Info "Running Python functional tests..."
            if (Test-Path "$repoRoot\tests\functional") {
                & $pythonExe -m pytest "$repoRoot\tests\functional" --junitxml="$repoRoot\test-results-functional.xml" -v --tb=short 2>$null
                if ($?) { Write-Success "Python functional tests completed" } else { Write-Warning-Message "Python functional tests failed or skipped" }
            } else {
                Write-Info "No tests/functional directory; skipping functional tests"
            }
        }

        if ($runIntegration) {
            Write-Info "Running Python integration tests (tests/edge_agent/integration)..."
            & $pythonExe -m pytest "$repoRoot\tests\edge_agent\integration" --junitxml="$repoRoot\test-results-integration.xml" -v --tb=short 2>$null
            if ($?) { Write-Success "Python integration tests completed" } else { Write-Warning-Message "Python integration tests failed or skipped" }
        }

        if ($runE2E) {
            Write-Info "Running Python e2e tests..."
            if (Test-Path "$repoRoot\tests\e2e") {
                & $pythonExe -m pytest "$repoRoot\tests\e2e" --junitxml="$repoRoot\test-results-e2e.xml" -v --tb=short 2>$null
                if ($?) { Write-Success "Python e2e tests completed" } else { Write-Warning-Message "Python e2e tests failed or skipped" }
            } else {
                Write-Info "No tests/e2e directory; skipping e2e tests"
            }
        }
    }

    if ($runTypeScript) {
        Write-Info "Checking Node.js installation for TypeScript tests..."
        $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
        if ($nodeCommand) {
            node --version | Out-Null
            Write-Success "Node.js is installed"
            $tsRoot = "offline-folder-rag\vscode-extension"
            if (Test-Path $tsRoot) {
                Push-Location $tsRoot
                try {
                    Write-Info "Installing TypeScript dependencies in $tsRoot..."
                    npm install --no-audit --no-fund
                    if ($?) { Write-Success "TypeScript dependencies installed" } else { Write-Warning-Message "npm install failed; TypeScript tests may be unreliable" }

                    $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
                    $hasBuild = $packageJson.scripts.PSObject.Properties.Name -contains "build"
                    if ($hasBuild) {
                        Write-Info "Building TypeScript..."
                        npm run build
                        if ($?) { Write-Success "TypeScript build completed" } else { Write-Warning-Message "TypeScript build failed" }
                    } else {
                        Write-Info "No build script in package.json; skipping TypeScript build"
                    }

                    $hasJest = (Test-Path "jest.config.js") -or (Test-Path "jest.config.ts")
                    if ($hasJest -and $runUnit) {
                        Write-Info "Running TypeScript unit tests..."
                        npx jest --testPathPattern="__tests__|tests" --no-cache 2>$null
                        if ($?) { Write-Success "TypeScript unit tests completed" } else { Write-Warning-Message "TypeScript unit tests failed or were skipped" }
                    } elseif (-not $hasJest) {
                        Write-Info "No Jest config in vscode-extension; skipping TypeScript unit tests"
                    }
                } finally {
                    Pop-Location
                }
            } else {
                Write-Warning-Message "offline-folder-rag\vscode-extension not found; skipping TypeScript steps"
            }
        } else {
            Write-Warning-Message "Node.js not found; skipping TypeScript/Jest tests"
        }
    }

    Write-Info "Stopping test services..."
    if (Test-Path "docker-compose.test.yml") {
        try {
            $downProcess = Start-Process -FilePath "docker" -ArgumentList "compose", "-f", "docker-compose.test.yml", "down" -NoNewWindow -Wait -PassThru
            if ($downProcess.ExitCode -ne 0) { Write-Warning-Message "Could not stop Docker services" }
        } catch {
            Write-Warning-Message "Could not stop Docker services"
        }
    }

    Write-Success "Tests stage completed"
}

# Stage 5: Build Docker Image
function Invoke-Build {
    Write-Section "STAGE 5: Build Docker Image"

    if ($SkipDocker) {
        Write-Warning-Message 'Docker build skipped (SkipDocker flag)'
        return
    }

    docker --version | Out-Null
    if (!$?) {
        Write-Error-Message "Docker not found. Cannot build image."
        return
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $gitCommit = git rev-parse --short HEAD 2>$null
    if (!$?) { $gitCommit = "unknown" }
    $gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if (!$?) { $gitBranch = "unknown" }

    # Build Confluence image (primary)
    $imageTagConfluence = "repo-analysis-rag/confluence:${gitBranch}-${timestamp}-${gitCommit}"
    Write-Info "Building Docker image: $imageTagConfluence (docker/Dockerfile.confluence)"
    $env:DOCKER_BUILDKIT = 0
    $buildDate = (Get-Date).ToUniversalTime().ToString("o")
    docker build -f docker/Dockerfile.confluence -t $imageTagConfluence --build-arg BUILD_DATE=$buildDate --build-arg VCS_REF=$gitCommit --build-arg VERSION="${gitBranch}-${timestamp}" .
    if ($?) {
        Write-Success "Docker image built successfully: $imageTagConfluence"
        Write-Info "To run: docker run -p 8000:8000 $imageTagConfluence"
    } else {
        Write-Error-Message "Docker build failed for Confluence image"
    }

    # Optionally build MCP image
    if (Test-Path "docker/Dockerfile.mcp") {
        $imageTagMcp = "repo-analysis-rag/mcp:${gitBranch}-${timestamp}-${gitCommit}"
        Write-Info "Building Docker image: $imageTagMcp (docker/Dockerfile.mcp)"
        docker build -f docker/Dockerfile.mcp -t $imageTagMcp --build-arg BUILD_DATE=$buildDate --build-arg VCS_REF=$gitCommit --build-arg VERSION="${gitBranch}-${timestamp}" .
        if ($?) {
            Write-Success "Docker image built successfully: $imageTagMcp"
        } else {
            Write-Warning-Message "Docker build failed for MCP image"
        }
    }
}

# Stage 6: Deploy
function Invoke-Deploy {
    Write-Section "STAGE 6: Deploy to Local Docker Compose"

    if ($SkipDocker) {
        Write-Warning-Message 'Docker deployment skipped (SkipDocker flag)'
        return
    }

    if (-not (Test-Path "docker-compose.yml")) {
        Write-Warning-Message "docker-compose.yml not found. Skipping deployment."
        return
    }

    Write-Info "Starting Docker Compose services (docker-compose.yml)..."
    docker compose -f docker-compose.yml up -d
    if ($?) {
        Write-Success "Services started"
        Write-Info "Services running:"
        docker compose -f docker-compose.yml ps
    } else {
        Write-Error-Message "Failed to start services"
    }
}

# Main execution
Write-Host "`n============================================"
Write-Host "  Repo_Analysis_Rag_Agent Local CI/CD     "
Write-Host "  Stage: $Stage"
Write-Host "============================================`n"

if ($Stage -eq 'all' -or $Stage -eq 'setup' -or $Stage -eq 'test') {
    Invoke-Setup
}

if ($Stage -eq 'all' -or $Stage -eq 'lint') {
    Invoke-Lint
}

if ($Stage -eq 'all' -or $Stage -eq 'security') {
    Invoke-Security
}

if ($Stage -eq 'all' -or $Stage -eq 'test') {
    Invoke-Tests
}

if ($Stage -eq 'all' -or $Stage -eq 'build') {
    Invoke-Build
}

if ($Stage -eq 'all' -or $Stage -eq 'deploy') {
    Invoke-Deploy
}

Write-Host 'Pipeline completed'
