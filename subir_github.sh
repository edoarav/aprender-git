#!/bin/bash

set -e

echo "======================================"
echo "  ACTUALIZAR PROYECTO EN GITHUB"
echo "======================================"

REPO="git@github.com:edoarav/aprender-git.git"
BRANCH="master"

# ======================================
# COMPROBAR PROYECTO
# ======================================

if [ ! -f "Gimnasio.py" ]; then
    echo "❌ No parece que estés en la carpeta del proyecto."
    exit 1
fi

# ======================================
# COMPROBAR .ENV
# ======================================

if [ -f ".env" ]; then
    echo "🔐 .env encontrado"
else
    echo "⚠️ No existe .env"
fi

# ======================================
# COMPROBAR .GITIGNORE
# ======================================

if ! grep -qxF ".env" .gitignore; then
    echo "❌ ERROR: .gitignore no contiene .env"
    echo "ABORTANDO para proteger las credenciales."
    exit 1
fi

echo "✅ .env está protegido por .gitignore"

# ======================================
# COMPROBAR REPOSITORIO
# ======================================

if [ ! -d ".git" ]; then
    echo "❌ No existe un repositorio Git."
    echo "Ejecuta git init primero."
    exit 1
fi

# ======================================
# COMPROBAR REMOTE
# ======================================

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️ Configurando origin..."
    git remote add origin "$REPO"
fi

# ======================================
# AGREGAR CAMBIOS
# ======================================

echo ""
echo "📋 Agregando cambios..."

git add .

# ======================================
# COMPROBAR QUE .ENV NO ESTE INCLUIDO
# ======================================

echo ""
echo "🔐 Verificando .env..."

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "❌ ERROR: .env está siendo seguido por Git."
    echo "ABORTANDO."
    exit 1
fi

echo "✅ .env NO será enviado."

# ======================================
# MOSTRAR CAMBIOS
# ======================================

echo ""
echo "📦 Cambios preparados:"
git status --short

# ======================================
# COMMIT
# ======================================

echo ""
read -p "💬 Mensaje del commit: " MENSAJE

if [ -z "$MENSAJE" ]; then
    echo "❌ El mensaje no puede estar vacío."
    exit 1
fi

git commit -m "$MENSAJE"

# ======================================
# PUSH
# ======================================

echo ""
echo "🚀 Subiendo a GitHub..."

git push -u origin "$BRANCH"


echo "======================================"
echo "  ✅ PROYECTO ACTUALIZADO"
echo "======================================"
