"""
Project Template - Template para nuevos proyectos
Copia este archivo como base para tus proyectos
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import time
from datetime import datetime

class ProjectTemplate:
    """Template base para proyectos de análisis"""
    
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_path = Path(f"projects/my_projects/{project_name}")
        self.config_file = self.project_path / "config.json"
        self.load_config()
    
    def load_config(self):
        """Cargar configuración del proyecto"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def log(self, message, level="INFO"):
        """Registrar mensaje con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def prepare_data(self):
        """Paso 1: Preparar datos"""
        self.log("Preparando datos...")
        # Tu código aquí
        self.log("✅ Datos preparados")
    
    def explore_data(self):
        """Paso 2: Explorar datos"""
        self.log("Explorando datos...")
        # Tu código aquí
        self.log("✅ Exploración completada")
    
    def train_model(self):
        """Paso 3: Entrenar modelo"""
        self.log("Entrenando modelo...")
        # Tu código aquí
        self.log("✅ Modelo entrenado")
    
    def evaluate_model(self):
        """Paso 4: Evaluar modelo"""
        self.log("Evaluando modelo...")
        # Tu código aquí
        self.log("✅ Evaluación completada")
    
    def generate_report(self):
        """Paso 5: Generar reporte"""
        self.log("Generando reporte...")
        # Tu código aquí
        self.log("✅ Reporte generado")
    
    def run(self):
        """Ejecutar pipeline completo"""
        self.log(f"Iniciando proyecto: {self.project_name}")
        
        try:
            self.prepare_data()
            self.explore_data()
            self.train_model()
            self.evaluate_model()
            self.generate_report()
            
            self.log("🎉 Proyecto completado exitosamente", "SUCCESS")
        
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            raise


# Ejemplo de uso personalizado
class SentimentAnalysisProject(ProjectTemplate):
    """Proyecto específico: Análisis de Sentimientos"""
    
    def prepare_data(self):
        self.log("Preparando tweets...")
        # Cargar tweets
        # Limpiar texto
        # Procesar
        self.log("✅ Tweets preparados")
    
    def train_model(self):
        self.log("Entrenando clasificador de sentimientos...")
        # Entrenar modelo
        self.log("✅ Modelo de sentimientos listo")


class PriceMonitoringProject(ProjectTemplate):
    """Proyecto específico: Monitoreo de Precios"""
    
    def prepare_data(self):
        self.log("Descargando precios históricos...")
        # Scraping de precios
        # Normalizar datos
        self.log("✅ Precios descargados")
    
    def train_model(self):
        self.log("Entrenando predictor de precios...")
        # Entrenar modelo de predicción
        self.log("✅ Predictor listo")


if __name__ == "__main__":
    # Ejemplo 1: Template básico
    project = ProjectTemplate("Proyecto Básico")
    project.run()
    
    # Ejemplo 2: Análisis de sentimientos
    # sentiment = SentimentAnalysisProject("Análisis de Sentimientos")
    # sentiment.run()
