"""
Project Manager - Gestor de Proyectos Locales
Crear, gestionar y exportar proyectos de análisis de datos
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import shutil

class ProjectManager:
    """Gestor centralizado de proyectos"""
    
    def __init__(self, base_path="projects/my_projects"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.projects_config = self.base_path / "projects.json"
        self.load_projects()
    
    def load_projects(self):
        """Cargar lista de proyectos"""
        if self.projects_config.exists():
            with open(self.projects_config, 'r', encoding='utf-8') as f:
                self.projects = json.load(f)
        else:
            self.projects = {}
    
    def save_projects(self):
        """Guardar lista de proyectos"""
        with open(self.projects_config, 'w', encoding='utf-8') as f:
            json.dump(self.projects, f, indent=2, ensure_ascii=False)
    
    def create_project(self, name, description="", project_type="general"):
        """Crear un nuevo proyecto con estructura"""
        
        if name in self.projects:
            print(f"❌ El proyecto '{name}' ya existe")
            return False
        
        project_path = self.base_path / name
        
        # Crear estructura de carpetas
        folders = [
            "data",
            "data/raw",
            "data/processed",
            "data/external",
            "scripts",
            "notebooks",
            "models",
            "results",
            "docs",
            "tests"
        ]
        
        for folder in folders:
            (project_path / folder).mkdir(parents=True, exist_ok=True)
        
        # Crear archivos iniciales
        self._create_project_files(project_path, name)
        
        # Registrar proyecto
        self.projects[name] = {
            "path": str(project_path),
            "type": project_type,
            "description": description,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }
        
        self.save_projects()
        
        print(f"✅ Proyecto '{name}' creado exitosamente")
        print(f"📁 Ruta: {project_path}")
        print(f"\nEstructura creada:")
        for folder in folders:
            print(f"  📂 {folder}")
        
        return True
    
    def _create_project_files(self, project_path, name):
        """Crear archivos iniciales del proyecto"""
        
        # README del proyecto
        readme_content = f"""# Proyecto: {name}

## Descripción
Describe tu proyecto aquí.

## Estructura
- `data/` - Datasets
- `scripts/` - Scripts Python
- `notebooks/` - Jupyter Notebooks
- `models/` - Modelos entrenados
- `results/` - Resultados del análisis

## Cómo usar

### Preparar datos
```python
python scripts/01_prepare_data.py
```

### Entrenar modelo
```python
python scripts/02_train_model.py
```

### Generar reportes
```python
python scripts/03_generate_report.py
```

## Dependencias
Instala con: `pip install -r requirements.txt`

## Autor
Tu nombre

## Fecha
Creado: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        with open(project_path / "README.md", 'w') as f:
            f.write(readme_content)
        
        # .gitignore del proyecto
        gitignore_content = """__pycache__/
*.pyc
.DS_Store
.ipynb_checkpoints/
*.pkl
*.joblib
*.csv
models/*.h5
models/*.pickle
results/*.json
.env
"""
        
        with open(project_path / ".gitignore", 'w') as f:
            f.write(gitignore_content)
        
        # requirements.txt vacío
        with open(project_path / "requirements.txt", 'w') as f:
            f.write("# Dependencias del proyecto\n")
        
        # config.json del proyecto
        config = {
            "project_name": name,
            "created": datetime.now().isoformat(),
            "ml_algorithm": None,
            "data_sources": [],
            "features": []
        }
        
        with open(project_path / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        # Script template
        script_template = f'''#!/usr/bin/env python3
"""
Script Template - {name}
"""

import pandas as pd
import numpy as np
from pathlib import Path

def main():
    print("🚀 Iniciando {name}...")
    
    # Tu código aquí
    
    print("✅ Completado")

if __name__ == "__main__":
    main()
'''
        
        with open(project_path / "scripts" / "main.py", 'w') as f:
            f.write(script_template)
    
    def list_projects(self):
        """Listar todos los proyectos"""
        if not self.projects:
            print("❌ No hay proyectos creados aún")
            return
        
        print("📋 PROYECTOS DISPONIBLES")
        print("=" * 70)
        
        for i, (name, info) in enumerate(self.projects.items(), 1):
            print(f"\n{i}. {name}")
            print(f"   Tipo: {info.get('type', 'N/A')}")
            print(f"   Descripción: {info.get('description', 'Sin descripción')}")
            print(f"   Creado: {info.get('created', 'N/A')[:10]}")
            print(f"   Ruta: {info.get('path', 'N/A')}")
    
    def open_project(self, name):
        """Abrir un proyecto (mostrar información)"""
        if name not in self.projects:
            print(f"❌ Proyecto '{name}' no encontrado")
            return False
        
        info = self.projects[name]
        project_path = Path(info['path'])
        
        print(f"\n📂 PROYECTO: {name}")
        print("=" * 70)
        print(f"Tipo: {info.get('type', 'N/A')}")
        print(f"Descripción: {info.get('description', 'Sin descripción')}")
        print(f"Creado: {info.get('created', 'N/A')}")
        print(f"Última modificación: {info.get('last_modified', 'N/A')}")
        print(f"Ruta: {project_path}")
        
        print(f"\n📁 Contenido:")
        if project_path.exists():
            for item in sorted(project_path.iterdir()):
                if item.is_dir():
                    print(f"  📂 {item.name}/")
                else:
                    print(f"  📄 {item.name}")
        
        # Mostrar archivos de datos
        data_path = project_path / "data" / "processed"
        if data_path.exists():
            files = list(data_path.glob("*"))
            if files:
                print(f"\n📊 Archivos de datos procesados:")
                for f in files:
                    size = f.stat().st_size / 1024  # KB
                    print(f"  📋 {f.name} ({size:.1f} KB)")
        
        return True
    
    def delete_project(self, name, confirm=True):
        """Eliminar un proyecto"""
        if name not in self.projects:
            print(f"❌ Proyecto '{name}' no encontrado")
            return False
        
        if confirm:
            response = input(f"⚠️  ¿Eliminar proyecto '{name}'? (s/n): ")
            if response.lower() != 's':
                print("Cancelado")
                return False
        
        project_path = Path(self.projects[name]['path'])
        shutil.rmtree(project_path)
        del self.projects[name]
        self.save_projects()
        
        print(f"✅ Proyecto '{name}' eliminado")
        return True
    
    def export_project(self, name, format_type="json"):
        """Exportar resultados del proyecto"""
        if name not in self.projects:
            print(f"❌ Proyecto '{name}' no encontrado")
            return False
        
        project_path = Path(self.projects[name]['path'])
        results_path = project_path / "results"
        
        if not results_path.exists():
            print(f"❌ No hay resultados en '{name}'")
            return False
        
        export_path = Path("exports") / name
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Copiar resultados
        for file in results_path.glob("*"):
            shutil.copy2(file, export_path / file.name)
        
        print(f"✅ Proyecto exportado a: {export_path}")
        return True
    
    def get_statistics(self):
        """Obtener estadísticas de proyectos"""
        print("\n📊 ESTADÍSTICAS DE PROYECTOS")
        print("=" * 70)
        print(f"Total de proyectos: {len(self.projects)}")
        
        types = {}
        for info in self.projects.values():
            ptype = info.get('type', 'general')
            types[ptype] = types.get(ptype, 0) + 1
        
        print(f"\nTipos de proyectos:")
        for ptype, count in types.items():
            print(f"  • {ptype}: {count}")
        
        # Tamaño total
        total_size = 0
        for info in self.projects.values():
            path = Path(info['path'])
            if path.exists():
                for file in path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
        
        print(f"\nTamaño total: {total_size / (1024*1024):.2f} MB")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Gestor de Proyectos para DataLens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python project_manager.py --create "Mi Análisis"
  python project_manager.py --list
  python project_manager.py --open "Mi Análisis"
  python project_manager.py --delete "Mi Análisis"
  python project_manager.py --export "Mi Análisis" --format json
  python project_manager.py --stats
        """
    )
    
    parser.add_argument('--create', type=str, help='Crear nuevo proyecto')
    parser.add_argument('--description', type=str, help='Descripción del proyecto')
    parser.add_argument('--type', type=str, default='general', 
                       help='Tipo de proyecto (general, ml, osint, scraping)')
    parser.add_argument('--list', action='store_true', help='Listar proyectos')
    parser.add_argument('--open', type=str, help='Abrir un proyecto')
    parser.add_argument('--delete', type=str, help='Eliminar proyecto')
    parser.add_argument('--export', type=str, help='Exportar proyecto')
    parser.add_argument('--format', type=str, default='json', 
                       help='Formato de exportación (json, csv, excel)')
    parser.add_argument('--stats', action='store_true', help='Ver estadísticas')
    
    args = parser.parse_args()
    
    manager = ProjectManager()
    
    if args.create:
        manager.create_project(
            args.create,
            description=args.description or "",
            project_type=args.type
        )
    
    elif args.list:
        manager.list_projects()
    
    elif args.open:
        manager.open_project(args.open)
    
    elif args.delete:
        manager.delete_project(args.delete)
    
    elif args.export:
        manager.export_project(args.export, args.format)
    
    elif args.stats:
        manager.get_statistics()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
