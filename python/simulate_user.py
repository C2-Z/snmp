import requests
import ftplib
import time
import random
import os
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import poplib

SERVER_IP = "192.168.30.10"
HTTP_PORT = 80
FTP_PORT = 21
MYSQL_PORT = 3306
SMTP_PORT = 25
POP3_PORT = 110
FTP_USER = "usuario1"
FTP_PASS = "pass123"
MAIL_USER = ["empleado1", "empleado2"]  # Lista de usuarios para alternar
MAIL_PASS = "pass123"  # Contraseña común
HTTP_URLS = [
    f"http://{SERVER_IP}:{HTTP_PORT}/",
    f"http://{SERVER_IP}:{HTTP_PORT}/dashboard/",
    f"http://{SERVER_IP}:{HTTP_PORT}/contacto.html",
    f"http://{SERVER_IP}:{HTTP_PORT}/imagen.html",
    f"http://{SERVER_IP}:{HTTP_PORT}/post1.html"
]
FTP_FILES = ["archivo.txt", "imagen.jpg"]

def simulate_http_session():
    """Simula una sesión HTTP con 80% GET y 20% POST solo para contacto.html."""
    for _ in range(random.randint(3, 6)):
        url = random.choice(HTTP_URLS)
        try:
            if url.endswith("contacto.html") and random.random() < 0.2:  # 20% probabilidad de POST
                data = {
                    "nombre": f"Empleado{random.randint(1, 50)}",
                    "email": f"empleado{random.randint(1, 50)}@corporacion.com",
                    "mensaje": f"Solicitud sobre {random.choice(['reunión', 'proyecto', 'soporte técnico'])}"
                }
                response = requests.post(url, data=data, timeout=5)
                status_msg = "Éxito" if response.status_code == 200 else "Error en formulario"
                print(f"Petición POST a {url}: Código {response.status_code} ({status_msg})")
                time.sleep(random.uniform(5, 15))  # Pausa de 5-15 segundos para formularios
            else:  # 80% GET para todas las URLs
                response = requests.get(url, timeout=5)
                status_msg = "Éxito" if response.status_code == 200 else "Archivo no encontrado o acceso denegado"
                print(f"Petición GET a {url}: Código {response.status_code} ({status_msg})")
                time.sleep(random.uniform(2, 10))  # Pausa de 2-10 segundos para navegación
        except Exception as e:
            print(f"Error HTTP: {e}")

def simulate_ftp_session():
    """Simula una sesión FTP con mayor variabilidad (descarga/subida/listado)."""
    try:
        ftp = ftplib.FTP()
        ftp.connect(SERVER_IP, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        num_actions = random.randint(1, 4)  # Aumentado a 1-4 para variabilidad
        for _ in range(num_actions):
            file = random.choice(FTP_FILES)
            action_type = random.choice(["download", "upload", "list"])  # 1/3 probabilidad cada una
            try:
                if action_type == "download":
                    with open(file, "wb") as f:
                        ftp.retrbinary(f"RETR {file}", f.write)
                    print(f"Descargado {file} vía FTP")
                    time.sleep(random.uniform(2, 10))  # Pausa corta para descarga
                elif action_type == "upload":
                    if not os.path.exists(file):
                        with open(file, "w") as f:
                            f.write(f"Contenido actualizado de {file} - Fecha: {time.ctime()}")  # Contenido variable
                    with open(file, "rb") as f:
                        ftp.storbinary(f"STOR {file}", f)
                    print(f"Subido {file} vía FTP")
                    time.sleep(random.uniform(5, 15))  # Pausa media para subida
                else:  # Listado
                    files = ftp.nlst()
                    print(f"Listado de archivos en FTP: {files}")
                    time.sleep(random.uniform(3, 12))  # Pausa para revisar listado
            except ftplib.error_perm:
                print(f"Error FTP con {file}: Archivo no encontrado o permiso denegado")
        ftp.quit()
    except Exception as e:
        print(f"Error FTP: {e}")

def simulate_mysql_session():
    """Simula una sesión MySQL con inserciones, consultas, actualizaciones y eliminaciones."""
    try:
        # Conexión a MySQL
        conn = mysql.connector.connect(
            host=SERVER_IP,
            user="root",
            password="",  # Cambia si configuraste una contraseña
            database="simulacion"
        )
        cursor = conn.cursor()
        
        num_actions = random.randint(1, 3)  # 1-3 operaciones por sesión
        for _ in range(num_actions):
            action_type = random.choice(["insert", "query", "update", "delete"])  # 25% cada una
            empleado = f"Empleado{random.randint(1, 50)}"
            if action_type == "insert":
                accion = random.choice(["Consulta de datos", "Actualización de reporte", "Revisión de proyecto"])
                cursor.execute(
                    "INSERT INTO actividades (empleado, accion, fecha) VALUES (%s, %s, NOW())",
                    (empleado, accion)
                )
                conn.commit()
                print(f"Inserción en MySQL: {empleado} - {accion} a las {time.ctime()}")
                time.sleep(random.uniform(2, 8))  # Pausa de 2-8 segundos
            elif action_type == "query":
                cursor.execute("SELECT * FROM actividades ORDER BY fecha DESC LIMIT 5")
                results = cursor.fetchall()
                print(f"Consulta en MySQL: Últimas 5 actividades - {results}")
                time.sleep(random.uniform(3, 10))  # Pausa de 3-10 segundos
            elif action_type == "update":
                cursor.execute("SELECT id FROM actividades LIMIT 1")
                if cursor.fetchone():
                    nuevo_accion = random.choice(["Revisión completada", "Tarea pospuesta", "Reporte finalizado"])
                    id_a_actualizar = random.randint(1, 100)
                    cursor.execute(
                        "UPDATE actividades SET accion = %s WHERE id = %s",
                        (nuevo_accion, id_a_actualizar)
                    )
                    conn.commit()
                    if cursor.rowcount > 0:
                        print(f"Actualización en MySQL: ID {id_a_actualizar} cambiado a {nuevo_accion} a las {time.ctime()}")
                    else:
                        print(f"Actualización en MySQL: No se encontró ID {id_a_actualizar} para actualizar")
                else:
                    print("Actualización en MySQL: No hay registros para actualizar")
                time.sleep(random.uniform(2, 8))  # Pausa de 2-8 segundos
            else:  # delete
                cursor.execute("SELECT id FROM actividades LIMIT 1")
                if cursor.fetchone():
                    id_a_eliminar = random.randint(1, 100)
                    cursor.execute(
                        "DELETE FROM actividades WHERE id = %s",
                        (id_a_eliminar,)
                    )
                    conn.commit()
                    if cursor.rowcount > 0:
                        print(f"Eliminación en MySQL: Registro con ID {id_a_eliminar} eliminado a las {time.ctime()}")
                    else:
                        print(f"Eliminación en MySQL: No se encontró ID {id_a_eliminar} para eliminar")
                else:
                    print("Eliminación en MySQL: No hay registros para eliminar")
                time.sleep(random.uniform(2, 8))  # Pausa de 2-8 segundos
        conn.close()
    except Exception as e:
        print(f"Error MySQL: {e}")

def simulate_mail_session():
    """Simula una sesión de correo con SMTP (envío) y POP3 (recepción)."""
    try:
        num_actions = random.randint(1, 2)  # 1-2 acciones por sesión
        for _ in range(num_actions):
            action_type = random.choice(["send", "receive"])  # 50/50 probabilidad
            if action_type == "send":
                # Envío SMTP con alternancia de remitente y destinatario
                sender = random.choice(MAIL_USER)
                receiver = MAIL_USER[1] if sender == MAIL_USER[0] else MAIL_USER[0]  # Alterna
                server = smtplib.SMTP(SERVER_IP, SMTP_PORT)
                server.ehlo()
                msg = MIMEMultipart()
                msg['From'] = f"{sender}@oficina.local"
                msg['To'] = f"{receiver}@oficina.local"
                msg['Subject'] = f"Reporte {random.choice(['diario', 'semanal', 'proyecto'])}"
                body = f"Contenido del email: Actualización sobre {random.choice(['reunión', 'tarea'])} - {time.ctime()}"
                msg.attach(MIMEText(body, 'plain'))
                server.sendmail(msg['From'], msg['To'], msg.as_string())
                server.quit()
                print(f"Email enviado de {sender} a {receiver} vía SMTP a las {time.ctime()}")
                time.sleep(random.uniform(5, 12))  # Pausa de 5-12 segundos
            else:  # Receive POP3
                # Recepción POP3
                current_user = random.choice(MAIL_USER)  # Alterna entre empleado1 y empleado2
                pop_server = poplib.POP3(SERVER_IP, POP3_PORT)
                pop_server.user(current_user)
                pop_server.pass_(MAIL_PASS)
                num_messages = len(pop_server.list()[1])
                if num_messages > 0:
                    # Obtiene el primer mensaje
                    response, msg_lines, octets = pop_server.retr(1)
                    print(f"Email recibido vía POP3 para {current_user}: {len(msg_lines)} líneas")
                else:
                    print(f"No hay emails en la bandeja de {current_user}")
                pop_server.quit()
                time.sleep(random.uniform(3, 8))  # Pausa de 3-8 segundos
    except Exception as e:
        print(f"Error Mail: {e}")

while True:
    print(f"Iniciando sesión simulada a las {time.ctime()}")
    actions = [simulate_http_session, simulate_ftp_session, simulate_mysql_session, simulate_mail_session]
    random.shuffle(actions)
    for action in actions:
        action()
        time.sleep(random.uniform(10, 30))
    wait_time = random.randint(300, 600)
    print(f"Esperando {wait_time / 60:.1f} minutos hasta la siguiente sesión...")
    time.sleep(wait_time)