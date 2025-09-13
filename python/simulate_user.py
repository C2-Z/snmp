import requests
import ftplib
import time
import random
import os

# Configuración (ajusta según tu setup)
SERVER_IP = "192.168.30.10"  # IP del servidor XAMPP (verifica con ipconfig)
HTTP_PORT = 80  # Puerto de Apache (cambia a 8080 si lo modificaste)
FTP_PORT = 21  # Puerto de FileZilla
FTP_USER = "usuario1"  # Usuario FTP configurado en FileZilla
FTP_PASS = "pass123"  # Contraseña FTP configurada en FileZilla
HTTP_URLS = [
    f"http://{SERVER_IP}:{HTTP_PORT}/",  # Raíz (carga index.html por defecto)
    f"http://{SERVER_IP}:{HTTP_PORT}/dashboard/"  # Usa el dashboard de XAMPP
]
FTP_FILES = ["archivo.txt", "imagen.jpg"]  # Archivos en la carpeta FTP

def simulate_http_session():
    """Simula una sesión HTTP (navegación web) con archivos de htdocs."""
    for _ in range(random.randint(3, 6)):  # 3-6 peticiones por sesión
        url = random.choice(HTTP_URLS)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Petición HTTP a {url}: Código {response.status_code} (Éxito)")
            else:
                print(f"Petición HTTP a {url}: Código {response.status_code} (Archivo no encontrado)")
            time.sleep(random.uniform(2, 10))  # Pausa humana (2-10 seg)
        except Exception as e:
            print(f"Error HTTP: {e}")

def simulate_ftp_session():
    """Simula una sesión FTP (descarga/subida) con la carpeta FTP."""
    try:
        ftp = ftplib.FTP()
        ftp.connect(SERVER_IP, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        for _ in range(random.randint(1, 3)):  # 1-3 acciones por sesión
            file = random.choice(FTP_FILES)
            try:
                if random.choice([True, False]):  # Descargar
                    with open(file, "wb") as f:
                        ftp.retrbinary(f"RETR {file}", f.write)
                    print(f"Descargado {file} vía FTP")
                else:  # Subir
                    if not os.path.exists(file):
                        with open(file, "w") as f: f.write(f"Contenido de {file}")
                    with open(file, "rb") as f:
                        ftp.storbinary(f"STOR {file}", f)
                    print(f"Subido {file} vía FTP")
                time.sleep(random.uniform(3, 15))  # Pausa humana (3-15 seg)
            except ftplib.error_perm:
                print(f"Error FTP con {file}: Archivo no encontrado o permiso denegado")
        ftp.quit()
    except Exception as e:
        print(f"Error FTP: {e}")

# Lógica principal: Simular usuario real
while True:
    print(f"Iniciando sesión simulada a las {time.ctime()}")
    actions = [simulate_http_session, simulate_ftp_session]
    random.shuffle(actions)  # Mezcla aleatoria de acciones
    for action in actions:
        action()
        time.sleep(random.uniform(10, 30))  # Pausa entre tipos de acciones (10-30 seg)
    wait_time = random.randint(300, 600)  # Pausa larga entre sesiones (5-10 min)
    print(f"Esperando {wait_time / 60:.1f} minutos hasta la siguiente sesión...")
    time.sleep(wait_time)