import socket
import threading
import json
import time
import traceback
from constants import DEFAULT_PORT, BUFFER_SIZE

class Network:
    def __init__(self, mode, ip=None, port=DEFAULT_PORT):
        self.mode = mode
        self.ip = ip if ip else socket.gethostbyname(socket.gethostname())
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id = 0  # ID del jugador local
        self.connected = False
        self.clients = []  # Lista de conexiones de clientes (solo para el host)
        self.game_state = None  # Estado del juego actual
        self.lock = threading.Lock()  # Para sincronización
        
        if mode == "host":
            self.host()
        else:
            self.join()
    
    def host(self):
        """Inicia el servidor"""
        try:
            # Intentar vincular a todas las interfaces (0.0.0.0) para permitir conexiones externas
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(13)  # Máximo 13 jugadores
            self.connected = True
            self.id = 0  # El host siempre es el jugador 0
            
            # Obtener la IP real para mostrar
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"Servidor iniciado en {local_ip}:{self.port}")
            print(f"También puedes usar 127.0.0.1:{self.port} para conexiones locales")
            
            # Iniciar hilo para aceptar conexiones
            threading.Thread(target=self.accept_connections, daemon=True).start()
        except Exception as e:
            print(f"Error al iniciar el servidor: {e}")
            traceback.print_exc()
    
    def join(self):
        """Se une a un servidor existente"""
        try:
            # Verificar si la IP incluye puerto
            if ':' in self.ip:
                self.ip, port_str = self.ip.split(':')
                self.port = int(port_str)
                print(f"Conectando a {self.ip}:{self.port}")
            
            # Intentar primero con la IP proporcionada
            self.socket.settimeout(10)  # Timeout de 5 segundos
            self.socket.connect((self.ip, self.port))
            self.connected = True
            
            # Recibir ID del servidor
            data = self.socket.recv(BUFFER_SIZE)
            self.id = int(data.decode())
            
            # Iniciar hilo para recibir mensajes
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            print(f"Conectado al servidor con ID {self.id}")
        except socket.gaierror:
            # Si hay error de resolución de nombres, intentar con localhost
            print(f"No se pudo resolver el nombre de host. Intentando con localhost...")
            try:
                self.ip = "127.0.0.1"
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10)
                self.socket.connect((self.ip, self.port))
                self.connected = True
                
                # Recibir ID del servidor
                data = self.socket.recv(BUFFER_SIZE)
                self.id = int(data.decode())
                
                # Iniciar hilo para recibir mensajes
                threading.Thread(target=self.receive_messages, daemon=True).start()
                
                print(f"Conectado al servidor con ID {self.id}")
            except Exception as e:
                print(f"Error al conectar con localhost: {e}")
                traceback.print_exc()
                self.connected = False
        except ConnectionRefusedError:
            print(f"Conexión rechazada. Asegúrate de que el servidor esté en ejecución y el puerto {self.port} esté abierto.")
            self.connected = False
        except Exception as e:
            print(f"Error al conectar con el servidor: {e}")
            traceback.print_exc()
            self.connected = False
    
    def accept_connections(self):
        """Acepta conexiones entrantes (solo para el host)"""
        while self.connected:
            try:
                client_socket, addr = self.socket.accept()
                
                # Asignar ID al cliente
                client_id = len(self.clients) + 1
                client_socket.send(str(client_id).encode())
                
                # Añadir cliente a la lista
                with self.lock:
                    self.clients.append({
                        'socket': client_socket,
                        'address': addr,
                        'id': client_id
                    })
                
                # Iniciar hilo para recibir mensajes del cliente
                threading.Thread(target=self.handle_client, args=(client_socket, client_id), daemon=True).start()
                
                print(f"Cliente {client_id} conectado desde {addr}")
                
                # Enviar el estado actual del juego al nuevo cliente si existe
                if self.game_state:
                    try:
                        # Dividir el mensaje en partes más pequeñas para evitar problemas de buffer
                        json_data = json.dumps({'game_state': self.game_state}, ensure_ascii=True)
                        
                        # Enviar en fragmentos de 1024 bytes
                        for i in range(0, len(json_data), 1024):
                            fragment = json_data[i:i+1024]
                            client_socket.send(fragment.encode('utf-8'))
                            time.sleep(0.01)  # Pequeña pausa para evitar saturación
                        
                        # Enviar un marcador de fin de mensaje
                        client_socket.send(b'<END>')
                        
                        print(f"Estado del juego enviado al cliente {client_id}")
                    except Exception as e:
                        print(f"Error al enviar estado inicial al cliente {client_id}: {e}")
                        traceback.print_exc()
            except Exception as e:
                print(f"Error al aceptar conexión: {e}")
                traceback.print_exc()
                break
    
    def handle_client(self, client_socket, client_id):
        """Maneja los mensajes de un cliente específico (solo para el host)"""
        buffer = b""
        
        while self.connected:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                
                # Acumular datos en el buffer
                buffer += data
                
                # Verificar si tenemos un mensaje completo
                if b'<END>' in buffer:
                    # Extraer el mensaje completo
                    message_data, buffer = buffer.split(b'<END>', 1)
                    
                    # Procesar el mensaje
                    try:
                        message = json.loads(message_data.decode('utf-8'))
                        
                        # Si es una acción del juego, procesarla
                        if 'action' in message:
                            self.process_action(message['action'])
                        
                        # Reenviar el estado del juego a todos los clientes
                        if self.game_state:
                            self.broadcast(json.dumps({'game_state': self.game_state}, ensure_ascii=True).encode('utf-8'))
                    except json.JSONDecodeError as e:
                        print(f"Error al decodificar mensaje del cliente {client_id}: {e}")
                        print(f"Datos recibidos: {message_data[:100]}...")  # Mostrar los primeros 100 caracteres
                        traceback.print_exc()
            
            except Exception as e:
                print(f"Error al manejar cliente {client_id}: {e}")
                traceback.print_exc()
                break
        
        # Eliminar cliente de la lista
        with self.lock:
            self.clients = [c for c in self.clients if c['id'] != client_id]
        
        print(f"Cliente {client_id} desconectado")
    
    def receive_messages(self):
        """Recibe mensajes del servidor (solo para clientes)"""
        buffer = b""
        
        while self.connected:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    break
                
                # Acumular datos en el buffer
                buffer += data
                
                # Procesar todos los mensajes completos en el buffer
                while b'<END>' in buffer:
    # Extraer el mensaje completo
                    message_data, buffer = buffer.split(b'<END>', 1)
                    
                    # Procesar cada objeto JSON individualmente si hay más de uno concatenado
                    decoded = message_data.decode('utf-8')
                    # Divide por '}{' para separar objetos JSON pegados
                    json_chunks = []
                    start = 0
                    for i in range(1, len(decoded)):
                        if decoded[i-1] == '}' and decoded[i] == '{':
                            json_chunks.append(decoded[start:i])
                            start = i
                    json_chunks.append(decoded[start:])

                    for chunk in json_chunks:
                        try:
                            message = json.loads(chunk)
                            # Actualizar el estado del juego
                            if 'game_state' in message:
                                with self.lock:
                                    self.game_state = message['game_state']
                                    print("Estado del juego actualizado correctamente")
                            elif 'start_game' in message:
                                print("Recibido mensaje de inicio de juego")
                        except json.JSONDecodeError as e:
                            print(f"Error al decodificar JSON: {e}")
                            print(f"Chunk recibido (primeros 100 bytes): {chunk[:100]}...")
                            traceback.print_exc()
            # Si no hay mensaje completo, esperar más datos

            except socket.timeout:
                print("Timeout al recibir datos, reintentando...")
                continue
            
            except Exception as e:
                print(f"Error al recibir mensajes: {e}")
                traceback.print_exc()
                break
        
        self.connected = False
        print("Desconectado del servidor")
    
    def send_action(self, action):
        """Envía una acción al servidor (solo para clientes)"""
        if not self.connected:
            return False
        
        try:
            # Serializar con ensure_ascii=True para evitar problemas con caracteres Unicode
            message = json.dumps({'action': action}, ensure_ascii=True).encode('utf-8')
            
            # Enviar el mensaje seguido de un marcador de fin
            self.socket.send(message)
            self.socket.send(b'<END>')
            
            return True
        except Exception as e:
            print(f"Error al enviar acción: {e}")
            traceback.print_exc()
            return False
    
    def send_game_state(self, game_state):
        """Envía el estado del juego a todos los clientes (solo para el host)"""
        if not self.connected or self.mode != "host":
            return False
        
        with self.lock:
            self.game_state = game_state
        
        try:
            # Convertir objetos complejos a tipos básicos de Python
            simplified_state = self._simplify_game_state(game_state)
            
            # Serializar con ensure_ascii=True para evitar problemas con caracteres Unicode
            json_data = json.dumps({'game_state': simplified_state}, ensure_ascii=True)
            
            # Enviar el mensaje seguido de un marcador de fin
            message = json_data.encode('utf-8') + b'<END>'
            
            return self.broadcast(message)
        except Exception as e:
            print(f"Error al serializar el estado del juego: {e}")
            print(f"Objeto problemático: {str(game_state)[:200]}...")  # Mostrar parte del objeto
            traceback.print_exc()
            return False
    
    def _simplify_game_state(self, obj):
        """Convierte objetos complejos a tipos básicos de Python para serialización JSON"""
        if isinstance(obj, dict):
            return {str(k): self._simplify_game_state(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._simplify_game_state(item) for item in obj]
        elif hasattr(obj, 'to_dict'):
            return self._simplify_game_state(obj.to_dict())
        elif isinstance(obj, (int, float, bool, str)) or obj is None:
            return obj
        else:
            # Convertir cualquier otro tipo a string para evitar problemas de serialización
            return str(obj)
    
    def broadcast(self, message):
        """Envía un mensaje a todos los clientes (solo para el host)"""
        if not self.connected or self.mode != "host":
            return False
        
        success = True
        with self.lock:
            for client in self.clients:
                try:
                    # Dividir el mensaje en fragmentos más pequeños si es necesario
                    if len(message) > 1024 and not message.endswith(b'<END>'):
                        # Si el mensaje no tiene ya un marcador de fin, dividirlo en fragmentos
                        for i in range(0, len(message) - 5, 1024):  # -5 para evitar cortar el <END>
                            fragment = message[i:i+1024]
                            client['socket'].send(fragment)
                            time.sleep(0.01)  # Pequeña pausa para evitar saturación
                    else:
                        # Enviar el mensaje completo
                        client['socket'].send(message)
                except Exception as e:
                    print(f"Error al enviar mensaje a cliente {client['id']}: {e}")
                    traceback.print_exc()
                    success = False
        
        return success
    
    def get_player_count(self):
        """Obtiene el número de jugadores conectados"""
        if self.mode == "host":
            return len(self.clients) + 1  # Clientes + host
        return 0
    
    def get_id(self):
        """Obtiene el ID del jugador local"""
        return self.id
    
    def is_host(self):
        """Verifica si el jugador local es el host"""
        return self.mode == "host"
    
    def start_game(self):
        """Inicia el juego (solo para el host)"""
        if not self.connected or self.mode != "host":
            return False
        
        # Enviar mensaje de inicio de juego
        message = json.dumps({'start_game': True}, ensure_ascii=True).encode('utf-8') + b'<END>'
        return self.broadcast(message)
    
    def receive_game_state(self):
        """Obtiene el estado del juego actual"""
        with self.lock:
            return self.game_state
    
    def process_action(self, action):
        """Procesa una acción recibida de un cliente (solo para el host)"""
        # Call the handler if set
        if hasattr(self, 'game_action_handler') and self.game_action_handler:
            self.game_action_handler(action)
    
    def close(self):
        """Cierra la conexión"""
        self.connected = False
        try:
            self.socket.close()
        except:
            pass

class NetworkOptimized:
    def __init__(self):
        self.compression = True  # Comprimir mensajes JSON
        self.delta_sync = True   # Solo enviar cambios, no estado completo
    
    def send_delta_update(self, changes):
        """Envía solo los cambios en lugar del estado completo"""
        compressed_data = self.compress_json(changes)
        return self.send(compressed_data)

# 2. Sistema de logging mejorado
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rummy_game.log'),
        logging.StreamHandler()
    ]
)

# 3. Configuración externa
import configparser
config = configparser.ConfigParser()
config.read('game_config.ini')

# 4. Tests unitarios
import unittest
class TestGameLogic(unittest.TestCase):
    def test_trio_formation(self):
        player = player(0, "Test")
        # Añadir cartas de prueba
        assert player._has_trio() == True

# 5. Persistencia de partidas
import pickle
def save_game_state(game, filename):
    with open(filename, 'wb') as f:
        pickle.dump(game.to_dict(), f)

def load_game_state(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)