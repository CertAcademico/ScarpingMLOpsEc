"""
Email Finder - Herramienta OSINT para encontrar emails
"""

import requests
from bs4 import BeautifulSoup
import re
import time

class EmailFinder:
    """Encuentra emails relacionados con un dominio"""
    
    def __init__(self, domain, delay=1):
        self.domain = domain
        self.delay = delay
        self.emails = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_emails_in_url(self, url):
        """Extrae emails de una URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar emails en href mailto
            for link in soup.find_all('a', href=re.compile(r'mailto:')):
                email = link.get('href').replace('mailto:', '')
                if self.domain in email:
                    self.emails.add(email)
            
            # Buscar emails en el contenido de texto
            text = soup.get_text()
            pattern = r'[a-zA-Z0-9._%+-]+@' + re.escape(self.domain)
            found_emails = re.findall(pattern, text)
            self.emails.update(found_emails)
            
            time.sleep(self.delay)
            return True
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def find_company_emails(self):
        """Intenta encontrar emails de la compañía"""
        print(f"🔍 Buscando emails de {self.domain}...")
        
        # URLs comunes donde se publican emails
        urls_to_check = [
            f"https://{self.domain}",
            f"https://www.{self.domain}",
            f"https://{self.domain}/contact",
            f"https://{self.domain}/about",
            f"https://{self.domain}/team",
        ]
        
        for url in urls_to_check:
            print(f"  📡 Verificando: {url}")
            self.find_emails_in_url(url)
        
        return list(self.emails)
    
    def get_emails(self):
        """Retorna los emails encontrados"""
        return sorted(list(self.emails))
    
    def save_to_file(self, filename):
        """Guarda los emails en un archivo"""
        with open(filename, 'w') as f:
            for email in sorted(self.emails):
                f.write(email + '\n')
        
        print(f"✅ {len(self.emails)} emails guardados en {filename}")


# Ejemplo de uso
if __name__ == "__main__":
    finder = EmailFinder("github.com")
    emails = finder.find_company_emails()
    
    print(f"\n✅ Emails encontrados: {len(emails)}")
    for email in emails[:5]:
        print(f"  📧 {email}")
    
    finder.save_to_file("emails.txt")
