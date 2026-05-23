"""
Data Preprocessing - Preprocesamiento de datos para ML
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer

class DataPreprocessor:
    """Preprocesa datos para machine learning"""
    
    def __init__(self, data):
        """Inicializar con datos (DataFrame, CSV o archivo Excel)"""
        if isinstance(data, str):
            if data.endswith('.csv'):
                self.data = pd.read_csv(data)
            elif data.endswith('.xlsx'):
                self.data = pd.read_excel(data)
            else:
                raise ValueError("Formato no soportado")
        else:
            self.data = data.copy()
        
        self.original_data = self.data.copy()
        print(f"📊 Datos cargados: {self.data.shape}")
    
    def get_info(self):
        """Mostrar información del dataset"""
        print("\n📋 INFORMACIÓN DEL DATASET")
        print("="*60)
        print(f"Filas: {self.data.shape[0]}")
        print(f"Columnas: {self.data.shape[1]}")
        
        print("\n🔍 Tipos de datos:")
        print(self.data.dtypes)
        
        print("\n⚠️ Valores faltantes:")
        missing = self.data.isnull().sum()
        print(missing[missing > 0])
        
        print("\n📈 Estadísticas:")
        print(self.data.describe())
    
    def handle_missing_values(self, strategy='mean'):
        """Manejar valores faltantes"""
        print(f"\n🔧 Manejando valores faltantes (estrategia: {strategy})...")
        
        imputer = SimpleImputer(strategy=strategy)
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        
        self.data[numeric_cols] = imputer.fit_transform(self.data[numeric_cols])
        
        print("✅ Valores faltantes manejados")
        return self
    
    def remove_duplicates(self):
        """Remover filas duplicadas"""
        initial = len(self.data)
        self.data = self.data.drop_duplicates()
        removed = initial - len(self.data)
        
        print(f"🗑️ {removed} filas duplicadas removidas")
        return self
    
    def remove_outliers(self, method='iqr', columns=None):
        """Remover outliers"""
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns
        
        initial = len(self.data)
        
        if method == 'iqr':
            for col in columns:
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                self.data = self.data[
                    (self.data[col] >= Q1 - 1.5 * IQR) &
                    (self.data[col] <= Q3 + 1.5 * IQR)
                ]
        
        elif method == 'zscore':
            from scipy import stats
            for col in columns:
                z_scores = np.abs(stats.zscore(self.data[col]))
                self.data = self.data[z_scores < 3]
        
        removed = initial - len(self.data)
        print(f"🎯 {removed} outliers removidos")
        return self
    
    def encode_categorical(self, columns=None):
        """Codificar variables categóricas"""
        if columns is None:
            columns = self.data.select_dtypes(include=['object']).columns
        
        self.encoders = {}
        
        for col in columns:
            encoder = LabelEncoder()
            self.data[col] = encoder.fit_transform(self.data[col].astype(str))
            self.encoders[col] = encoder
            print(f"✅ {col}: {len(encoder.classes_)} clases codificadas")
        
        return self
    
    def scale_features(self, method='standard', columns=None):
        """Escalar características numéricas"""
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        else:
            raise ValueError("Método no válido")
        
        self.data[columns] = scaler.fit_transform(self.data[columns])
        self.scaler = scaler
        
        print(f"📏 Características escaladas con {method} scaler")
        return self
    
    def drop_columns(self, columns):
        """Eliminar columnas"""
        self.data = self.data.drop(columns=columns)
        print(f"🗑️ {len(columns)} columnas eliminadas")
        return self
    
    def get_data(self):
        """Obtener datos procesados"""
        return self.data
    
    def save(self, filename):
        """Guardar datos procesados"""
        if filename.endswith('.csv'):
            self.data.to_csv(filename, index=False)
        elif filename.endswith('.xlsx'):
            self.data.to_excel(filename, index=False)
        
        print(f"💾 Datos guardados en {filename}")
    
    def reset(self):
        """Reiniciar a datos originales"""
        self.data = self.original_data.copy()
        print("🔄 Datos reiniciados")
        return self


# Ejemplo de uso
if __name__ == "__main__":
    # Crear datos de ejemplo
    data = pd.DataFrame({
        'edad': [25, 30, None, 35, 40],
        'ingreso': [30000, 50000, 60000, 55000, None],
        'ciudad': ['Madrid', 'Barcelona', 'Madrid', 'Madrid', 'Barcelona'],
        'estado': ['Activo', 'Inactivo', 'Activo', 'Activo', 'Inactivo']
    })
    
    # Preprocesar
    processor = DataPreprocessor(data)
    
    processor.get_info()
    processor.handle_missing_values()
    processor.remove_duplicates()
    processor.encode_categorical(['ciudad', 'estado'])
    processor.scale_features(method='standard')
    
    print("\n✅ Preprocesamiento completado")
    print(processor.get_data())
