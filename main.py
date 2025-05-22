import pygame
import sys
import time
import traceback
from constants import *
from game import Game
from network import Network
from ui import UI

def main():
    pygame.init()
    pygame.display.set_caption("Rummy 500")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # Pantalla inicial para elegir entre host o unirse
    network_mode = None
    ip_address = ""
    port = DEFAULT_PORT
    input_active = False
    input_text = ""
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, 300, 32)
    
    while network_mode is None:
        screen.fill(BG_COLOR)
        
        # Dibujar título
        title_font = pygame.font.SysFont(None, 48)
        title_text = title_font.render("Rummy 500", True, TEXT_COLOR)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Dibujar botones
        font = pygame.font.SysFont(None, 32)
        host_text = font.render("Crear partida", True, TEXT_COLOR)
        join_text = font.render("Unirse a partida", True, TEXT_COLOR)
        
        host_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 200, 50)
        join_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30, 200, 50)
        
        pygame.draw.rect(screen, BUTTON_COLOR, host_rect, border_radius=5)
        pygame.draw.rect(screen, BUTTON_COLOR, join_rect, border_radius=5)
        
        screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))
        screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
        
        # Si está en modo de unirse, mostrar campo de entrada para IP
        if input_active:
            # Instrucciones
            info_text = font.render("Introduce IP:Puerto (ej: 127.0.0.1:5555)", True, TEXT_COLOR)
            screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
            
            pygame.draw.rect(screen, INPUT_ACTIVE_COLOR if input_active else INPUT_INACTIVE_COLOR, input_rect, border_radius=5)
            input_surface = font.render(input_text, True, TEXT_COLOR)
            screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
            
            # Botón de confirmar
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 50, 120, 32)
            pygame.draw.rect(screen, BUTTON_COLOR, confirm_rect, border_radius=5)
            confirm_text = font.render("Confirmar", True, TEXT_COLOR)
            screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width() // 2, confirm_rect.centery - confirm_text.get_height() // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if host_rect.collidepoint(event.pos):
                    network_mode = "host"
                elif join_rect.collidepoint(event.pos):
                    input_active = True
                elif input_active and confirm_rect.collidepoint(event.pos):
                    network_mode = "join"
                    ip_address = input_text
            
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        network_mode = "join"
                        ip_address = input_text
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
    
    # Inicializar red
    try:
        network = Network(network_mode, ip_address, port)
    except Exception as e:
        print(f"Error al inicializar la red: {e}")
        traceback.print_exc()
        font = pygame.font.SysFont(None, 32)
        error_text = font.render(f"Error de inicialización: {str(e)[:50]}", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main()  # Reiniciar el juego
        return
    
    # Si no se pudo conectar y es cliente, volver al menú principal
    if network_mode == "join" and not network.connected:
        font = pygame.font.SysFont(None, 32)
        error_text = font.render("Error de conexión. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main()  # Reiniciar el juego
        return
    
    # Esperar a que todos los jugadores se conecten si es host
    if network_mode == "host":
        waiting = True
        player_count = 1  # El host cuenta como un jugador
        
        while waiting:
            screen.fill(BG_COLOR)
            
            # Dibujar mensaje de espera
            wait_text = font.render(f"Esperando jugadores... ({player_count}/13)", True, TEXT_COLOR)
            screen.blit(wait_text, (SCREEN_WIDTH // 2 - wait_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            
            # Mostrar información de conexión
            ip_info = font.render(f"Los jugadores pueden conectarse a:", True, TEXT_COLOR)
            screen.blit(ip_info, (SCREEN_WIDTH // 2 - ip_info.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            
            # Obtener IP local
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            ip_text = font.render(f"{local_ip}:{DEFAULT_PORT} o 127.0.0.1:{DEFAULT_PORT} (local)", True, TEXT_COLOR)
            screen.blit(ip_text, (SCREEN_WIDTH // 2 - ip_text.get_width() // 2, SCREEN_HEIGHT // 2 - 75))
            
            # Botón para iniciar juego
            start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
            pygame.draw.rect(screen, BUTTON_COLOR if player_count >= 2 else DISABLED_BUTTON_COLOR, start_rect, border_radius=5)
            start_text = font.render("Iniciar juego", True, TEXT_COLOR)
            screen.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height() // 2))
            
            pygame.display.flip()
            
            # Actualizar número de jugadores conectados
            player_count = network.get_player_count()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_rect.collidepoint(event.pos) and player_count >= 2:
                        waiting = False
                        network.start_game()
    
    # Inicializar juego
    try:
        game = Game(network)
        ui = UI(screen)
        if network.is_host():
            network.game_action_handler = game.handle_network_action
    except Exception as e:
        print(f"Error al inicializar el juego: {e}")
        traceback.print_exc()
        font = pygame.font.SysFont(None, 32)
        error_text = font.render(f"Error de inicialización del juego: {str(e)[:50]}", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main()  # Reiniciar el juego
        return
    
    # Esperar a que el juego se inicialice completamente
    waiting_for_init = True
    wait_start_time = time.time()
    timeout = 30  # Aumentado a 30 segundos para dar más tiempo
    
    while waiting_for_init and network.connected and time.time() - wait_start_time < timeout:
        screen.fill(BG_COLOR)
        font = pygame.font.SysFont(None, 32)
        wait_text = font.render("Esperando inicialización del juego...", True, TEXT_COLOR)
        screen.blit(wait_text, (SCREEN_WIDTH // 2 - wait_text.get_width() // 2, SCREEN_HEIGHT // 2))
        
        # Mostrar tiempo restante
        time_left = int(timeout - (time.time() - wait_start_time))
        time_text = font.render(f"Timeout en {time_left} segundos", True, TEXT_COLOR)
        screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        
        # Mostrar estado de la conexión
        conn_text = font.render(f"Conectado: {'Sí' if network.connected else 'No'}", True, TEXT_COLOR)
        screen.blit(conn_text, (SCREEN_WIDTH // 2 - conn_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))
        
        # Mostrar información de depuración
        debug_text = font.render(f"ID: {network.id}, Modo: {network.mode}", True, TEXT_COLOR)
        screen.blit(debug_text, (SCREEN_WIDTH // 2 - debug_text.get_width() // 2, SCREEN_HEIGHT // 2 + 120))
        
        pygame.display.flip()
        
        # Verificar si el juego ya tiene estado
        game_state = network.receive_game_state()
        if game_state is not None:
            print("Estado del juego recibido, iniciando juego...")
            waiting_for_init = False
        
        # Procesar eventos mientras esperamos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Pequeña pausa para no saturar la CPU
        pygame.time.delay(100)
    
    # Si se agotó el tiempo de espera, volver al menú principal
    if waiting_for_init:
        font = pygame.font.SysFont(None, 32)
        error_text = font.render("Tiempo de espera agotado. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main()  # Reiniciar el juego
        return
    
    # Bucle principal del juego
    running = True
    while running and network.connected:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Procesar eventos del juego
            if event.type == pygame.MOUSEBUTTONDOWN:
                ui.handle_click(event.pos, game)
            
            game.handle_event(event)
        
        # Actualizar estado del juego
        game.update()
        
        # Renderizar
        screen.fill(BG_COLOR)
        ui.draw(game)
        pygame.display.flip()
        
        clock.tick(FPS)
    
    # Si se desconectó, mostrar mensaje
    if not network.connected:
        font = pygame.font.SysFont(None, 32)
        error_text = font.render("Conexión perdida. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main()  # Reiniciar el juego
        return
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
