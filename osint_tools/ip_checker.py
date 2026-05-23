"""
IP Checker - Información detallada de direcciones IP
"""

import requests
import json
from typing import Dict, Any

class IPChecker:
    """Analiza y obtiene información de direcciones IP"""
    
    def __init__(self, ip_address):
        self.ip = ip_address
        self.info = {}
    
    def get_geolocation(self) -> Dict[str, Any]:
        """Obtiene información geográfica de una IP"""
        try:
            # Usar ip-api.com (gratuito)
            url = f"http://ip-api.com/json/{self.ip}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data['status'] == 'success':
                self.info['geolocation'] = {
                    'country': data.get('country'),
                    'region': data.get('regionName'),
                    'city': data.get('city'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'timezone': data.get('timezone'),
                }
                return self.info['geolocation']
            else:
                return {'error': data.get('message', 'Unknown error')}
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_isp(self) -> Dict[str, Any]:
        """Obtiene información del ISP"""
        try:
            url = f"http://ip-api.com/json/{self.ip}?fields=isp,org,as"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            self.info['isp'] = {
                'provider': data.get('isp'),
                'organization': data.get('org'),
                'asn': data.get('as')
            }
            return self.info['isp']
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """Análisis completo de la IP"""
        print(f"🔍 Analizando IP: {self.ip}")
        
        result = {
            'ip': self.ip,
            'geolocation': self.get_geolocation(),
            'isp': self.get_isp()
        }
        
        return result
    
    def is_vpn(self) -> bool:
        """Intenta detectar si es una VPN/Proxy"""
        try:
            # Usar ipqualityscore (limitado pero gratuito)
            url = f"https://ipqualityscore.com/api/json/ip/{self.ip}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return data.get('is_vpn', False)
        except:
            return None
    
    def print_report(self):
        """Imprime un reporte formateado"""
        analysis = self.get_full_analysis()
        
        print(f"\n{'='*60}")
        print(f"IP REPORT: {self.ip}")
        print(f"{'='*60}")
        
        geo = analysis.get('geolocation', {})
        if 'error' not in geo:
            print(f"\n🌍 GEOLOCATION:")
            print(f"  País: {geo.get('country')}")
            print(f"  Region: {geo.get('region')}")
            print(f"  Ciudad: {geo.get('city')}")
            print(f"  Coords: {geo.get('latitude')}, {geo.get('longitude')}")
            print(f"  Timezone: {geo.get('timezone')}")
        
        isp = analysis.get('isp', {})
        if 'error' not in isp:
            print(f"\n🏢 ISP:")
            print(f"  Proveedor: {isp.get('provider')}")
            print(f"  Organización: {isp.get('organization')}")
            print(f"  ASN: {isp.get('asn')}")
        
        vpn = self.is_vpn()
        if vpn is not None:
            print(f"\n🔐 SEGURIDAD:")
            print(f"  VPN/Proxy: {'Sí ⚠️' if vpn else 'No ✓'}")
        
        print(f"\n{'='*60}\n")


# Ejemplo de uso
if __name__ == "__main__":
    # Analizar Google DNS
    checker = IPChecker("8.8.8.8")
    checker.print_report()
    
    # Guardar resultado en JSON
    analysis = checker.get_full_analysis()
    with open("ip_report.json", 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print("✅ Reporte guardado en ip_report.json")
