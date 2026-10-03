# Prepara (solo si hace falta) y corre el sistema con GPU en Windows (sala Turing).
# Un solo comando, desde la carpeta del repositorio:
#   powershell -ExecutionPolicy Bypass -File turing.ps1                                       (ensayo: muestra, preguntas 1 a 3)
#   powershell -ExecutionPolicy Bypass -File turing.ps1 -Split test -Inicio 1 -Fin 165 -Tag sabado_1
# Si se interrumpe, se relanza el mismo comando y sigue donde quedo.
param(
    [string]$Split = "sample",
    [int]$Inicio = 1,
    [int]$Fin = 3,
    [string]$Tag = "ensayo"
)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$sitio = Join-Path $PSScriptRoot ".venv\Lib\site-packages"

function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Fallo($texto) { Write-Host "`nERROR: $texto" -ForegroundColor Red; exit 1 }
function Py {
    & $py @args
    if ($LASTEXITCODE -ne 0) { Fallo "fallo: python $($args -join ' ')" }
}

# 1. GPU visible para el sistema
Paso "GPU"
if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { Fallo "no se encuentra nvidia-smi: la maquina no tiene GPU NVIDIA o le falta el driver." }
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

# 2. Archivos necesarios
if (-not (Test-Path "build\indice\index.faiss")) { Fallo "falta build\indice (copie la carpeta build del paquete)." }
if ((Test-Path ".env") -and (Select-String -Path ".env" -Pattern "^\s*DECODER_.*qwen" -Quiet)) {
    Fallo ".env fija Qwen: borre o cambie las lineas DECODER_MODEL, DECODER_GGUF_REPO y DECODER_GGUF_FILE (Gemma es el valor por defecto)."
}

# 3. Entorno de Python
if (-not (Test-Path $py)) {
    Paso "Creando el entorno .venv"
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.11 -m venv .venv }
    if (-not (Test-Path $py)) { & python -m venv .venv }
    if (-not (Test-Path $py)) { Fallo "no se pudo crear .venv: instale Python 3.11 de python.org." }
}

# llama-cpp en Windows necesita las DLL de CUDA (cudart, cublas); se toman de las que trae torch.
function Copiar-DllCuda {
    $origen = Join-Path $sitio "torch\lib"
    $destino = Join-Path $sitio "llama_cpp\lib"
    if ((Test-Path $origen) -and (Test-Path $destino)) {
        Get-ChildItem $origen -Filter "*.dll" | Where-Object { $_.Name -match "^(cudart|cublas|cublasLt)64_" } |
            ForEach-Object { Copy-Item $_.FullName $destino -Force }
    }
}

$chequeo = "import torch, llama_cpp; print(torch.cuda.is_available(), llama_cpp.llama_supports_gpu_offload())"
function Estado-Gpu { Copiar-DllCuda; return ("" + (& $py -c $chequeo 2>$null)).Trim() }

if ((Estado-Gpu) -ne "True True") {
    Paso "Instalando dependencias (la primera vez tarda unos minutos)"
    Py -m pip install --upgrade pip
    Py -m pip install -r requirements.txt
    Paso "torch con CUDA (cu126)"
    Py -m pip install --force-reinstall --no-deps "torch==2.14.0" --index-url https://download.pytorch.org/whl/cu126
    Paso "llama-cpp-python con CUDA (cu125, rueda para Windows)"
    Py -m pip install --force-reinstall --no-deps "llama-cpp-python==0.3.35" --only-binary llama-cpp-python --index-url https://abetlen.github.io/llama-cpp-python/whl/cu125
}

Paso "Verificando que torch y llama-cpp usen la GPU"
$estado = Estado-Gpu
Write-Host "torch.cuda / llama_cpp GPU: $estado"
if ($estado -ne "True True") {
    & $py -c $chequeo
    Fallo "la GPU no quedo disponible (copie este mensaje completo)."
}

# 4. Corrida
Paso "Corriendo: --split $Split --rango $Inicio $Fin --tag $Tag"
& $py run.py --split $Split --gpu --indice-existente --rango $Inicio $Fin --tag $Tag
exit $LASTEXITCODE
