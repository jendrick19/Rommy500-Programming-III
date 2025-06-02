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
    icon = pygame.image.load("balatro.jpg")
    icon = pygame.transform.smoothscale(icon, (130, 165))
    clock = pygame.time.Clock()
    last_broadcast= time.time()
    broadcast_interval = 2  # Intervalo de broadcast en segundos
    
    # Pantalla inicial para elegir entre host o unirse
    network_mode = None
    ip_address = ""
    port = DEFAULT_PORT
    input_active = False
    input_text = ""
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, 300, 32)
    showing_rules = False

    while network_mode is None:
        screen.fill(BG_COLOR)
        if showing_rules:
            rules_font = pygame.font.SysFont(None, 24)
            rules_texts = [
                "Reglas del Rummy 500:",
                "Objetivo: evitar alcanzar o superar los 500 puntos.",
                "El ganador es quien tenga la menor puntuación total o el último que no haya llegado a 500 puntos.",
                "Jugadores: 2-13. Se usa un mazo de 52 cartas + 2 Joker. cada 3 jugadores se añade un mazo extra.",
                "Cómo Jugar:",
                "Cada jugador recibe 10 cartas. Se inicia un descarte central. Un jugador es designado MANO.",
                "El MANO tiene la primera opción de tomar la carta central. Si la toma, descarta una carta para mantener 10 en mano.",
                "Si el MANO no la toma, otros jugadores pueden hacerlo",
                "Pero el primero que la tome roba una carta adicional del mazo como penalización, quedando con 12 cartas.",
                "Si nadie la toma, la carta se quema (descarta).",
                "Durante el turno regular, el jugador puede:",
                "- Tomar la carta superior del mazo boca abajo (si no tomó la central o si fue por penalización).",
                "- Bajarse: Mostrar combinaciones válidas sobre la mesa. Se puede usar un Joker para completar una combinación, ",
                "y un Joker ya bajado puede ser reemplazado por la carta que representa y usado en otra combinación propia.",
                "- Agregar cartas: Añadir cartas a sus propias combinaciones ya bajadas.",
                "- Descartar: Colocar una carta boca arriba para terminar el turno.",
                "Combinaciones:",
                "- Trío: Tres cartas del mismo valor.",
                "- Seguidilla: Cuatro cartas consecutivas del mismo palo.",
                "Rondas de Juego (Combinaciones Requeridas para Bajarse):",
                "- Un Trío y una Seguidilla.",
                "- Dos Seguidillas.",
                "- Tres Tríos.",
                "- Ronda Completa: Una Seguidilla y Dos Tríos. Para finalizar, deben descartarse las diez cartas en un solo turno.",
                "Puntuación:",
                "- Cartas 2-9: 5 puntos.",
                "- Cartas 10-K: 10 puntos.",
                "- As: 15 puntos.",
                "- Joker: 25 puntos. Al final de una ronda, los jugadores que no se bajaron suman los puntos de las cartas en su mano.",
                "Fin de la Ronda: Termina cuando un jugador se queda sin cartas al bajar todas sus combinaciones (y descartar si es necesario). ",
                "Este jugador actuará primero en la siguiente ronda.",
                "Fin de la Partida: El juego sigue por las cuatro rondas hasta que quede solo un jugador con menos de 500 puntos.",
            ]
            for i, line in enumerate(rules_texts):
                text_surface = rules_font.render(line, True, TEXT_COLOR)
                screen.blit(text_surface,(20, 20 + i * 21))
            pygame.display.flip()
        elif input_active:
            font = pygame.font.SysFont(None, 32)
            info_text = font.render("Introduce IP:Puerto (ej: 127.0.0.1:5555)", True, TEXT_COLOR)
            screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
            pygame.draw.rect(screen, INPUT_ACTIVE_COLOR, input_rect, border_radius=5)
            input_surface = font.render(input_text, True, TEXT_COLOR)
            screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
            # Botón de confirmar
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 50, 120, 32)
            pygame.draw.rect(screen, BUTTON_COLOR, confirm_rect, border_radius=5)
            confirm_text = font.render("Confirmar", True, TEXT_COLOR)
            screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width() // 2, confirm_rect.centery - confirm_text.get_height() // 2))
            pygame.display.flip()
        else:
            # Dibujar título
            title_font = pygame.font.SysFont(None, 48)
            title_text = title_font.render("Rummy 500", True, TEXT_COLOR)
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
            
            icon_rect = icon.get_rect(center=(SCREEN_WIDTH // 2, 170))
            screen.blit(icon, icon_rect)
            # Dibujar botones
            font = pygame.font.SysFont(None, 32)
            host_text = font.render("Crear partida", True, TEXT_COLOR)
            join_text = font.render("Unirse a partida", True, TEXT_COLOR)
            rules_text = font.render("Reglas", True, TEXT_COLOR)
            
            host_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 90, 200, 50)
            join_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20, 200, 50)
            rules_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 70, 200, 50)
            
            pygame.draw.rect(screen, BUTTON_COLOR, host_rect, border_radius=5)
            pygame.draw.rect(screen, BUTTON_COLOR, join_rect, border_radius=5)
            pygame.draw.rect(screen, BUTTON_COLOR, rules_rect, border_radius=5)

            
            screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))
            screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
            screen.blit(rules_text, (rules_rect.centerx - rules_text.get_width() // 2, rules_rect.centery - rules_text.get_height() // 2))
            pygame.display.flip()
        # Si está en modo de unirse, mostrar campo de entrada para IP
           
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if showing_rules:
                # Cerrar reglas con cualquier clic o tecla
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    showing_rules = False

            elif input_active:
                # Procesar solo eventos de input
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if confirm_rect.collidepoint(event.pos):
                        network_mode = "join"
                        ip_address = input_text
                        input_active = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        network_mode = "join"
                        ip_address = input_text
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

            else:
                # Procesar eventos normales del menú
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_rect.collidepoint(event.pos):
                        network_mode = "host"
                    elif join_rect.collidepoint(event.pos):
                        input_active = True
                    elif rules_rect.collidepoint(event.pos):
                        showing_rules = True
        
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
        print(f"[MAIN] Soy el jugador local con ID: {game.player_id}")
        import os

        try:
            font_path = os.path.join("DejaVuSans.ttf")
            card_font = pygame.font.Font(font_path, 32)
        except:
            card_font = pygame.font.SysFont("dejavusans", 32)

        ui = UI(screen, card_font=card_font)
        if hasattr(game, "cards_to_deal"):
            ui.animate_deal(game)  # Animación antes de repartir

            # Ahora sí, reparte las cartas realmente
            for player, cards in zip(game.players, game.cards_to_deal):
                player.add_to_hand(cards)
            del game.cards_to_deal  # Limpia el atributo temporal
            # Si eres host, sincroniza el estado actualizado
            if network.is_host():
                network.send_game_state(game.to_dict())
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
            print("Recibido estado → discard_offered_to:", game.discard_offered_to, "| Yo soy:", game.player_id)
        
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
    showing_round_scores = False
    last_game_state = None

    while running and network.connected:
        # Enviar el estado periódicamente SOLO si eres host
        if network.is_host() and (time.time() - last_broadcast > broadcast_interval):
            network.send_game_state(game.to_dict())
            last_broadcast = time.time()
        # Procesar todos los eventos una sola vez
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
               running = False

            # Manejar pantalla de puntuación de ronda
            if showing_round_scores:
                ui.draw_round_scores(game, is_host=network.is_host())
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    ui.handle_click(event.pos, game)
                    # Solo el host puede iniciar la siguiente ronda
                    if network.is_host():
                        # Envía el resumen de puntuación a los clientes antes de iniciar la nueva rondas
                        print("[HOST] Iniciando nueva ronda")
                        showing_round_scores = False
                        game.start_new_round()
                        print(f"[HOST] Estado tras iniciar nueva ronda: ronda={game.round_num}, jugador={game.current_player_idx}, estado={game.state}")
                    network.send_game_state(game.to_dict())
                continue  # No procesar más eventos si estamos mostrando puntuación

            # Procesar eventos del juego normalmente
            if event.type == pygame.MOUSEBUTTONDOWN:
                ui.handle_click(event.pos, game)
            game.handle_event(event)

        

        # Detectar cambios en el estado del juego para mostrar/ocultar pantalla de puntuación
        if game.state != last_game_state:
            print(f"[{('HOST' if network.is_host() else 'CLIENTE')}] Cambio de estado: {last_game_state} -> {game.state}")

            if game.state == GAME_STATE_ROUND_END and not showing_round_scores:
                print(f"[{('HOST' if network.is_host() else 'CLIENTE')}] Mostrando pantalla de puntuación")

                showing_round_scores = True
                print(f"Mostrando pantalla de puntuación. Host: {network.is_host()}")

            elif game.state == GAME_STATE_PLAYING and showing_round_scores:
                print(f"[{('HOST' if network.is_host() else 'CLIENTE')}] Mostrando pantalla de puntuación")
                showing_round_scores = False
                print("Ocultando pantalla de puntuación, nueva ronda iniciada")
                if network.is_host():
                   network.send_game_state(game.to_dict())  # Enviar estado actualizado a clientes
            last_game_state = game.state
                


        # Actualizar estado del juego
        game.update()
        # Renderizar
        screen.fill(BG_COLOR)
        ui.draw(game)
        pygame.display.flip()
        clock.tick(FPS)
    
    # Si se desconectó, mostrar mensaje
    if not network.connected:
        print(f"[{('HOST' if network.is_host() else 'CLIENTE')}] Desconectado del servidor")
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
