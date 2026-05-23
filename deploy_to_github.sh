#!/bin/bash
# 📤 DEPLOY A GITHUB - DataLens (Versión Profesional)

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🚀 DEPLOY A GITHUB - DataLens Intelligence             ║"
echo "║        Web Scraping + OSINT + Machine Learning                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# PASO 1: VALIDAR INSTALACIÓN
# ============================================
echo "📌 PASO 1: Validar Git"
echo "───────────────────────────────────────"

if ! command -v git &> /dev/null; then
    echo "❌ Git no está instalado"
    echo "Instálalo desde: https://git-scm.com/download"
    exit 1
fi

git_version=$(git --version)
echo "✅ $git_version"
echo ""

# ============================================
# PASO 2: INICIALIZAR REPOSITORIO
# ============================================
echo "📌 PASO 2: Inicializar Git"
echo "───────────────────────────────────────"

if [ -d .git ]; then
    echo "✅ Repositorio Git ya existe"
else
    git init
    echo "✅ Repositorio Git inicializado"
fi

# Configurar usuario (si no está configurado)
if ! git config user.name &> /dev/null; then
    echo ""
    read -p "Tu nombre completo: " user_name
    read -p "Tu email: " user_email
    
    git config --global user.name "$user_name"
    git config --global user.email "$user_email"
    echo "✅ Usuario configurado: $user_name <$user_email>"
fi

echo ""

# ============================================
# PASO 3: CREAR .GITIGNORE
# ============================================
echo "📌 PASO 3: Crear .gitignore"
echo "───────────────────────────────────────"

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Jupyter Notebook
.ipynb_checkpoints
*.ipynb

# Data
datasets/raw/
datasets/external/
*.csv
*.xlsx
*.xls
*.db

# Models
models/*.pkl
models/*.joblib
models/*.h5
models/*.pth

# Results
results/*.json
results/*.pdf
results/*.png

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Temporary
temp/
tmp/
*.tmp
EOF

echo "✅ .gitignore creado"
echo ""

# ============================================
# PASO 4: AGREGAR ARCHIVOS
# ============================================
echo "📌 PASO 4: Agregar archivos"
echo "───────────────────────────────────────"

git add .
echo "✅ Archivos agregados"

# Ver archivos a subir
echo ""
echo "📋 Archivos que se subirán:"
echo ""
git diff --cached --name-only | head -20

count=$(git diff --cached --name-only | wc -l)
echo ""
echo "Total: $count archivos"
echo ""

# ============================================
# PASO 5: CREAR COMMIT
# ============================================
echo "📌 PASO 5: Crear commit inicial"
echo "───────────────────────────────────────"

commit_message="🚀 Initial commit: DataLens - Web Scraping + OSINT + ML

- Web scraping con BeautifulSoup4
- Herramientas OSINT profesionales
- Módulos de Machine Learning
- Gestor de proyectos integrado
- Templates para nuevos proyectos
- Datasets y almacenamiento local"

git commit -m "$commit_message"
echo "✅ Commit realizado"
echo ""

# ============================================
# PASO 6: CONFIGURAR GITHUB REMOTE
# ============================================
echo "📌 PASO 6: Configurar GitHub"
echo "───────────────────────────────────────"
echo ""
echo "⚠️  IMPORTANTE:"
echo "1. Ve a https://github.com/new"
echo "2. Nombre: DataLens"
echo "3. Descripción: Web Scraping + OSINT + Machine Learning para Especialistas en Datos"
echo "4. Elige 'Public'"
echo "5. NO inicialices con README"
echo "6. Copia la URL (HTTPS recomendado)"
echo ""

read -p "¿Ya creaste el repositorio? (s/n): " repo_created

if [ "$repo_created" != "s" ]; then
    echo "Por favor crea el repositorio en https://github.com/new y vuelve"
    exit 1
fi

echo ""
read -p "Pega la URL de tu repositorio GitHub: " github_url

if [ -z "$github_url" ]; then
    echo "❌ URL vacía"
    exit 1
fi

# Agregar remote
git remote add origin "$github_url" 2>/dev/null || git remote set-url origin "$github_url"
echo "✅ Remote agregado"
echo ""

# ============================================
# PASO 7: SUBIR A GITHUB
# ============================================
echo "📌 PASO 7: Subir a GitHub"
echo "───────────────────────────────────────"

git branch -M main
echo "✅ Rama configurada como 'main'"

echo ""
echo "⏳ Subiendo al repositorio..."
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ ¡ÉXITO! Proyecto subido a GitHub"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🔗 URL: $github_url"
    echo ""
    echo "📊 Próximos pasos:"
    echo "  1. Comparte el enlace: $github_url"
    echo "  2. Agrega más herramientas OSINT"
    echo "  3. Crea ejemplos de proyectos"
    echo "  4. Pide stars ⭐"
    echo ""
    echo "📚 Para usar localmente:"
    echo "  git clone $github_url"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
else
    echo ""
    echo "⚠️ Algo salió mal. Posibles soluciones:"
    echo ""
    echo "1️⃣ Error de autenticación HTTPS:"
    echo "   • En GitHub: Settings > Developer settings > Personal access tokens"
    echo "   • Genera un nuevo token con 'repo' permission"
    echo "   • Usa el token como contraseña"
    echo ""
    echo "2️⃣ Error de autenticación SSH:"
    echo "   • Configura SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
    echo "   • Luego usa URL SSH en lugar de HTTPS"
    echo ""
    echo "3️⃣ Ver detalles del error:"
    echo "   git push -u origin main -vv"
    echo ""
    exit 1
fi
