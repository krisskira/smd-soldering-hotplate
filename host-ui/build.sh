#!/bin/sh
# Compila HotPlate Studio a un binario nativo con Nuitka.
#
#   ./build.sh            binario optimizado (LTO, un solo ejecutable)
#   ./build.sh --quick    compilación rápida, sin LTO (para probar)
#   ./build.sh --debug    sin optimizaciones y con consola (para depurar)
#   ./build.sh --app      además genera HotPlateStudio.app (solo macOS)
#
# El binario queda en dist/. Los .json (tema, rampas, autoajuste) no se
# empaquetan: el programa los lee y escribe junto al ejecutable.
set -eu

cd "$(dirname "$0")"

QUICK=0
DEBUG=0
APP=0
for arg in "$@"; do
    case "$arg" in
        --quick) QUICK=1 ;;
        --debug) DEBUG=1 ;;
        --app) APP=1 ;;
        -h|--help)
            sed -n '2,12p' "$0"
            exit 0
            ;;
        *)
            echo "Opción desconocida: $arg (usa --help)" >&2
            exit 2
            ;;
    esac
done

# --- compilador de C: clang del sistema, o el de Xcode si no está en PATH ---
if ! command -v clang >/dev/null 2>&1; then
    if xcrun --find clang >/dev/null 2>&1; then
        export PATH="$(dirname "$(xcrun --find clang)"):$PATH"
    else
        echo "No hay compilador de C. Instala las herramientas: xcode-select --install" >&2
        exit 1
    fi
fi

# --- intérprete: el del venv del repo si existe ---
if [ -n "${PYTHON:-}" ]; then
    PY="$PYTHON"
elif [ -x "../.venv/bin/python" ]; then
    PY="../.venv/bin/python"
else
    PY="python3"
fi

if ! "$PY" -c "import nuitka" >/dev/null 2>&1; then
    echo "Instalando Nuitka en $($PY -c 'import sys; print(sys.prefix)')…"
    "$PY" -m pip install -q "nuitka>=2.4"
fi

JOBS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"

# matplotlib y el backend Tk se descubren en tiempo de ejecución: hay que
# incluirlos a mano. pyserial se sigue solo desde los imports.
set -- \
    --standalone \
    --onefile \
    --output-dir=dist \
    --output-filename=HotPlateStudio \
    --remove-output \
    --assume-yes-for-downloads \
    --jobs="$JOBS" \
    --enable-plugin=tk-inter \
    --include-package=matplotlib \
    --include-package=serial \
    --include-package=PIL \
    --include-module=matplotlib.backends.backend_tkagg \
    --nofollow-import-to=unittest \
    --nofollow-import-to=setuptools \
    --nofollow-import-to=pytest \
    --nofollow-import-to=numpy.testing \
    --nofollow-import-to=matplotlib.tests \
    --noinclude-pytest-mode=nofollow \
    --noinclude-setuptools-mode=nofollow \
    --python-flag=no_docstrings,isolated \
    --company-name="SMI" \
    --product-name="HotPlate Studio" \
    --macos-app-mode=gui

# --- nivel de optimización ---
if [ "$DEBUG" -eq 1 ]; then
    set -- "$@" --no-deployment
else
    set -- "$@" --deployment
    if [ "$QUICK" -eq 0 ]; then
        set -- "$@" --lto=yes
    fi
fi

# --- .app de macOS (atajo con icono; el binario suelto se genera siempre) ---
if [ "$APP" -eq 1 ]; then
    set -- "$@" --macos-create-app-bundle
fi

echo "Compilando con $PY (clang $(clang --version | head -1))…"
"$PY" -m nuitka "$@" app.py

BIN="dist/HotPlateStudio"
if [ -f "$BIN" ]; then
    strip -u -r -x "$BIN" 2>/dev/null || true
    echo ""
    echo "Listo: $BIN ($("$PY" -c "import os; print(f'{os.path.getsize(\"$BIN\")/1048576:.1f} MB')"))"
fi
