#!/bin/bash

set -e

echo "======================================"
echo "  SUBIR PROYECTO LIMPIO A GITHUB"
echo "======================================"

# ======================================
# CONFIGURACIÓN
# ======================================

REPO="git@github.com:edoarav/aprender-git.git"
BRANCH="master"

# ======================================
# COMPROBAR QUE ESTAMOS EN EL PROYECTO
# ======================================

if [ ! -f "Gimnasio.py" ]; then
    echo "❌ No parece que estés en la carpeta del proyecto."
    echo "Ejecuta este script desde ~/programas/Git"
    exit 1
fi

# ======================================
# COMPROBAR .ENV
# ======================================

if [ ! -f ".env" ]; then
    echo "⚠️ No existe .env"
    echo "Continuando..."
else
    echo "🔐 .env encontrado"
fi

# ======================================
# COMPROBAR .GITIGNORE
# ======================================

if ! grep -qxF ".env" .gitignore; then
    echo "❌ ERROR: .gitignore no contiene .env"
    echo "No voy a continuar para evitar subir credenciales."
    exit 1
fi

echo "✅ .env está protegido por .gitignore"

# ======================================
# BORRAR HISTORIAL GIT ANTERIOR
# ======================================

if [ -d ".git" ]; then
    echo "🗑️ Eliminando historial Git anterior..."
    rm -rf .git
fi

# ======================================
# CREAR REPOSITORIO NUEVO
# ======================================

echo "📦 Inicializando Git..."

git init
git branch -M "$BRANCH"

# ======================================
# CONFIGURAR REMOTO
# ======================================

git remote add origin "$REPO"

# ======================================
# AGREGAR ARCHIVOS
# ======================================

echo "📋 Agregando archivos..."

git add .

# ======================================
# VERIFICACIÓN DE SEGURIDAD
# ======================================

echo ""
echo "🔍 Archivos que serán enviados:"
echo ""

git status --short

echo ""
echo "🔐 Comprobando que .env NO esté incluido..."

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "❌ ERROR: .env está siendo incluido."
    echo "ABORTANDO."
    exit 1
fi

echo "✅ .env NO será enviado."

# ======================================
# COMMIT
# ======================================

echo ""
echo "💾 Creando commit..."

git commit -m "Proyecto inicial limpio"

# ======================================
# PUSH
# ======================================

echo ""
echo "🚀 Subiendo a GitHub..."

git push -u origin "$BRANCH"

echo ""
echo "======================================"
echo "  ✅ PROYECTO SUBIDO CORRECTAMENTE"
echo "======================================"
