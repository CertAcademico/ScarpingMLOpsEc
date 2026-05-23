#!/bin/bash
# 📤 Comandos para Subir BeautifulSoup4 a GitHub

echo "🚀 SUBIENDO PROYECTO A GITHUB"
echo "=============================="
echo ""

# ============================================
# PASO 1: INICIALIZAR GIT (si no está)
# ============================================
echo "📌 PASO 1: Inicializar Git"
echo "---"

if [ ! -d .git ]; then
    git init
    echo "✓ Repositorio Git inicializado"
else
    echo "✓ Git ya estaba inicializado"
fi

echo ""

# ============================================
# PASO 2: AGREGAR ARCHIVOS
# ============================================
echo "📌 PASO 2: Agregar archivos"
echo "---"

git add .
echo "✓ Todos los archivos agregados"

echo ""

# ============================================
# PASO 3: CREAR COMMIT INICIAL
# ============================================
echo "📌 PASO 3: Crear commit inicial"
echo "---"

git commit -m "Initial commit: BeautifulSoup4 tutorial completo con ejemplos y ejercicios"
echo "✓ Commit realizado"

echo ""

# ============================================
# PASO 4: CREAR REMOTE (si no existe)
# ============================================
echo "📌 PASO 4: Configurar remote a GitHub"
echo "---"

echo "⚠️  IMPORTANTE: Necesitas tener un repositorio creado en GitHub"
echo ""
echo "Instrucciones:"
echo "1. Ve a https://github.com/new"
echo "2. Nombre del repositorio: BeautifulSoup4"
echo "3. Descripción: Tutorial completo de BeautifulSoup4 con ejemplos y ejercicios"
echo "4. Elige 'Public' para que sea visible"
echo "5. NO inicialices con README (lo tienes aquí)"
echo "6. Copia la URL HTTPS o SSH"
echo ""

read -p "¿Ya creaste el repositorio? (s/n): " confirmar

if [ "$confirmar" != "s" ]; then
    echo "Por favor, crea el repositorio primero en https://github.com/new"
    exit 1
fi

echo ""

# Preguntar por la URL del repositorio
read -p "Pega la URL de tu repositorio GitHub (HTTPS o SSH): " github_url

if [ -z "$github_url" ]; then
    echo "❌ Error: Debes proporcionar una URL válida"
    exit 1
fi

# Agregar remote
git remote add origin "$github_url"
echo "✓ Remote agregado correctamente"

echo ""

# ============================================
# PASO 5: SUBIR A GITHUB
# ============================================
echo "📌 PASO 5: Subir a GitHub"
echo "---"

git branch -M main
echo "✓ Rama cambiada a 'main'"

echo ""
echo "⏳ Subiendo archivos a GitHub..."

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡ÉXITO! Tu proyecto está en GitHub"
    echo ""
    echo "🔗 URL: $github_url"
    echo ""
else
    echo ""
    echo "⚠️  Algo salió mal. Posibles soluciones:"
    echo ""
    echo "1️⃣  Si es error de autenticación SSH:"
    echo "    git remote set-url origin <URL_HTTPS>"
    echo ""
    echo "2️⃣  Si es error de autenticación HTTPS:"
    echo "    - En GitHub: Settings > Developer settings > Personal access tokens"
    echo "    - Copia el token y úsalo como contraseña"
    echo ""
    echo "3️⃣  Para ver errores detallados:"
    echo "    git push -u origin main -vv"
    exit 1
fi

echo ""
echo "=============================="
echo "📊 ESTADO DEL REPOSITORIO"
echo "=============================="
echo ""

git log --oneline -3
echo ""

git status
echo ""

echo "✨ ¡Listo! Tu proyecto está en GitHub"
echo ""
echo "Próximos pasos:"
echo "  • Comparte el enlace: $github_url"
echo "  • Agrega más ejemplos"
echo "  • Crea Issues para mejoras"
echo "  • Pide stars ⭐"
echo ""
