import pygame
import sys
import time
import traceback
import textwrap
import socket
from constants import * # Asegúrate de que 'ORANGE' esté definido aquí

def main():
    pygame.init()
    pygame.display.set_caption("Rummy 500")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        icon = pygame.image.load("balatro.jpg")
        icon = pygame.transform.smoothscale(icon, (200, 200))
    except pygame.error:
        print("Advertencia: No se pudo cargar 'balatro.jpg'. Usando un ícono predeterminado o ninguno.")
        icon = None
    
    clock = pygame.time.Clock()
    
    network_mode = None
    ip_address = ""
    port = DEFAULT_PORT
    input_active = False
    input_text = ""
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, 300, 32)
    showing_rules = False

    # Variables para el desplazamiento de las reglas
    scroll_offset = 0
    scroll_speed = 20 # Velocidad de desplazamiento con la rueda del ratón
    
    # Fuentes
    font = pygame.font.SysFont("Arial", 32)
    title_font = pygame.font.SysFont("Arial", 60, bold=True)
    small_font = pygame.font.SysFont("Arial", 20)

    # NUEVA FUENTE PARA LOS SUBTÍTULOS DE LAS REGLAS
    subtitle_rules_font = pygame.font.SysFont("Arial", 28, bold=True) # Fuente un poco más grande y en negrita para subtítulos
    
    # Configuración de fuente y espaciado para las reglas
    rules_font_size = 22
    rules_font = pygame.font.SysFont("Arial", rules_font_size)
    # line_spacing ya no se usará para calcular la altura total, pero se mantiene para el dibujo.
    # Una estimación de espaciado para las líneas de texto normales.
    line_spacing = rules_font.get_linesize() + 10 

    # Lista de los subtítulos para fácil referencia
    subtitles_list = [
        "Objetivo:", "Jugadores:", "Cómo Jugar:", "Durante un turno regular, el jugador puede:",
        "Combinaciones Válidas (Bajadas):", "Rondas de Juego (Requisitos para Bajarse por Primera Vez):",
        "Puntuación:", "Fin de la Ronda:", "Fin de la Partida:"
    ]

    # Contenido de las reglas (manteniendo el mismo orden)
    raw_rules_texts = [
        "Reglas del Rummy 500:",
        "",
        "Objetivo:",
        "El objetivo principal es evitar alcanzar o superar los 500 puntos. El ganador es quien tenga la menor puntuación total o el último que no haya llegado a 500 puntos.",
        "",
        "Jugadores:",
        "Se puede jugar con 2 a 13 jugadores. Se usa un mazo de 52 cartas + 2 Jokers. Por cada 3 jugadores adicionales, se añade un mazo extra.",
        "",
        "Cómo Jugar:",
        "Cada jugador recibe 10 cartas. Se inicia un descarte central. Un jugador es designado MANO (el primero en jugar la ronda).",
        "El MANO tiene la primera opción de tomar la carta central. Si la toma, debe descartar una carta para mantener 10 en mano.",
        "Si el MANO no la toma, los otros jugadores pueden hacerlo en orden de turno. Sin embargo, el primero que la tome roba una carta adicional del mazo como penalización, quedando con 12 cartas.",
        "Si nadie toma la carta central, se quema (se descarta y no se puede usar).",
        "",
        "Durante un turno regular, el jugador puede:",
        "- Tomar la carta superior del mazo boca abajo (si no tomó la central o si fue por penalización).",
        "- Bajarse: Mostrar combinaciones válidas sobre la mesa. Se puede usar un Joker para completar una combinación, y un Joker ya bajado puede ser reemplazado por la carta que representa y usado en otra combinación propia.",
        "- Agregar cartas: Añadir cartas a sus propias combinaciones ya bajadas o a las de otros jugadores en la mesa.",
        "- Descartar: Colocar una carta boca arriba para terminar el turno. Es obligatorio descartar al final del turno.",
        "",
        "Combinaciones Válidas (Bajadas):",
        "- Trío: Tres o más cartas del mismo valor (ej: 7♦ 7♥ 7♠).",
        "- Seguidilla: Cuatro o más cartas consecutivas del mismo palo (ej: 4♣ 5♣ 6♣ 7♣).",
        "",
        "Rondas de Juego (Requisitos para Bajarse por Primera Vez):",
        "- Ronda 1: Un Trío y una Seguidilla.",
        "- Ronda 2: Dos Seguidillas.",
        "- Ronda 3: Tres Tríos.",
        "- Ronda 4 (Completa): Una Seguidilla y Dos Tríos. Para finalizar esta ronda, deben descartarse las diez cartas en un solo turno (ir 'de una').",
        "",
        "Puntuación:",
        "- Cartas 2-9: 5 puntos.",
        "- Cartas 10, J, Q, K: 10 puntos.",
        "- As (A): 15 puntos.",
        "- Joker: 25 puntos.",
        "Al final de una ronda, los jugadores que no lograron bajarse suman los puntos de las cartas restantes en su mano. Los jugadores que se bajaron no suman puntos de penalización en esa ronda.",
        "",
        "Fin de la Ronda:",
        "Una ronda termina cuando un jugador se queda sin cartas, ya sea bajando todas sus combinaciones y descartando la última carta (si es necesario), o bajando todas sus cartas en una 'Ronda Completa'. El jugador que termina la ronda actuará primero en la siguiente.",
        "",
        "Fin de la Partida:",
        "El juego continúa a lo largo de las cuatro rondas. La partida finaliza cuando solo queda un jugador con menos de 500 puntos, o cuando se juegan las cuatro rondas y el jugador con la menor puntuación total es el ganador."
    ]

    # Pre-procesar las reglas para la visualización (wrapping de texto)
    wrapped_rules = []
    wrap_character_width = 85
    for line in raw_rules_texts:
        wrapped_lines = textwrap.wrap(line, width=wrap_character_width)
        wrapped_rules.extend(wrapped_lines)
    
    # --- Modificaciones para el cálculo de la altura de las reglas ---
    # Calcular la altura total que ocupa todo el texto de las reglas dinámicamente
    rules_display_area_start_y = 120 # Donde el texto de las reglas empieza
    rules_display_area_end_y = SCREEN_HEIGHT - 80 # Donde el área de desplazamiento termina visiblemente
    rules_display_area_height = rules_display_area_end_y - rules_display_area_start_y

    # Calcular la altura total real del contenido de las reglas
    rules_total_rendered_height = 0
    temp_y_calc = 0
    for line in wrapped_rules:
        if line in subtitles_list:
            temp_y_calc += 10 # Espacio extra antes de un subtítulo
            rules_total_rendered_height += 10 + subtitle_rules_font.get_linesize()
        else:
            rules_total_rendered_height += rules_font.get_linesize()
        # Agregar un espaciado adicional para cada línea si es necesario,
        # o puedes integrar este espaciado en la altura de la línea.
        # Para simplificar y asegurar que se vea todo, sumamos el espaciado entre líneas.
        rules_total_rendered_height += 10 # Espaciado adicional entre líneas

    # Añadir un poco de "relleno" al final si es necesario para asegurarse de que la última línea no quede cortada
    rules_total_rendered_height += 50 # Un buffer extra al final

    # --- Fin de modificaciones ---

    while network_mode is None:
        screen.fill(BG_COLOR)

        if showing_rules:
            rules_bg_color = (40, 80, 60)
            pygame.draw.rect(screen, rules_bg_color, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), border_radius=10)
            
            rules_title_text = title_font.render("Reglas del Rummy 500", True, TEXT_COLOR)
            screen.blit(rules_title_text, (SCREEN_WIDTH // 2 - rules_title_text.get_width() // 2, 40)) 

            current_y = rules_display_area_start_y - scroll_offset # Empezar el texto de las reglas más abajo del título

            for line in wrapped_rules:
                text_surface = None
                if line in subtitles_list:
                    current_y_to_draw = current_y + 10 # Añadir espacio antes del subtítulo para el dibujo
                    text_surface = subtitle_rules_font.render(line, True, ORANGE)
                else:
                    current_y_to_draw = current_y # No añadir espacio extra para líneas normales
                    text_surface = rules_font.render(line, True, TEXT_COLOR)
                
                # Solo dibuja si la línea está dentro del área visible de desplazamiento
                if current_y_to_draw + text_surface.get_height() > rules_display_area_start_y and \
                   current_y_to_draw < rules_display_area_end_y:
                    screen.blit(text_surface, (40, current_y_to_draw))
                
                # Actualizar current_y para la siguiente línea en base a la altura de la línea actual
                if line in subtitles_list:
                    current_y += 10 + subtitle_rules_font.get_linesize() + 10 # Espacio extra + altura del subtítulo + espacio
                else:
                    current_y += rules_font.get_linesize() + 10 # Altura de la línea + espacio

            # Ajuste para el cálculo de la barra de desplazamiento
            if rules_total_rendered_height > rules_display_area_height:
                # La barra de desplazamiento debe reflejar la porción visible del contenido total
                # La altura de la barra se basa en la proporción del área visible al total
                scroll_bar_height = (rules_display_area_height / rules_total_rendered_height) * (SCREEN_HEIGHT - 80)
                
                # El offset máximo para el scroll es la altura total del contenido menos el área visible
                max_scroll_offset = rules_total_rendered_height - rules_display_area_height
                
                # Asegurarse de que max_scroll_offset no sea negativo
                max_scroll_offset = max(0, max_scroll_offset)

                if max_scroll_offset > 0:
                    scroll_bar_y_relative_pos = (scroll_offset / max_scroll_offset)
                else:
                    scroll_bar_y_relative_pos = 0
                
                # Calcular la posición Y de la barra de desplazamiento dentro de su propio track
                # El track va de 40 a SCREEN_HEIGHT - 40. La altura del track es (SCREEN_HEIGHT - 80).
                scroll_bar_y = 40 + scroll_bar_y_relative_pos * ( (SCREEN_HEIGHT - 80) - scroll_bar_height)
                
                # Dibujar el track de la barra
                pygame.draw.rect(screen, (100, 100, 100), (SCREEN_WIDTH - 30, 40, 10, SCREEN_HEIGHT - 80), border_radius=5)
                # Dibujar la barra en sí
                pygame.draw.rect(screen, (200, 200, 200), (SCREEN_WIDTH - 30, scroll_bar_y, 10, scroll_bar_height), border_radius=5)

            close_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 60, 150, 40)
            pygame.draw.rect(screen, DARK_BLUE, close_button_rect, border_radius=5)
            close_text = font.render("Cerrar", True, TEXT_COLOR)
            screen.blit(close_text, (close_button_rect.centerx - close_text.get_width() // 2, close_button_rect.centery - close_text.get_height() // 2))

            pygame.display.flip()

        elif input_active:
            info_text = font.render("Introduce IP:Puerto (ej: 127.0.0.1:5555)", True, TEXT_COLOR)
            screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
            pygame.draw.rect(screen, INPUT_ACTIVE_COLOR, input_rect, border_radius=5)
            input_surface = font.render(input_text, True, TEXT_COLOR)
            text_x = input_rect.x + 5
            if input_surface.get_width() > input_rect.width - 10:
                text_x = input_rect.x + input_rect.width - input_surface.get_width() - 5
            screen.blit(input_surface, (text_x, input_rect.y + 5))
            
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 50, 120, 32)
            pygame.draw.rect(screen, DARK_BLUE, confirm_rect, border_radius=5)
            confirm_text = small_font.render("Confirmar", True, TEXT_COLOR)
            screen.blit(confirm_text, (confirm_rect.centerx - confirm_text.get_width() // 2, confirm_rect.centery - confirm_text.get_height() // 2))
            pygame.display.flip()
        else:
            # Dibujar título del menú principal
            title_text = title_font.render("Rummy 500", True, TEXT_COLOR)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.15))
            screen.blit(title_text, title_rect)
            
            if icon:
                icon_rect = icon.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.40))
                screen.blit(icon, icon_rect)

            # Dibujar botones del menú principal
            button_width = 300
            button_height = 60
            button_spacing = 25

            total_buttons_height = (button_height * 3) + (button_spacing * 2)
            start_y = (SCREEN_HEIGHT // 2) + (SCREEN_HEIGHT * 0.1)

            host_rect = pygame.Rect(SCREEN_WIDTH // 2 - (button_width // 2), start_y, button_width, button_height)
            join_rect = pygame.Rect(SCREEN_WIDTH // 2 - (button_width // 2), start_y + button_height + button_spacing, button_width, button_height)
            rules_rect = pygame.Rect(SCREEN_WIDTH // 2 - (button_width // 2), start_y + (button_height + button_spacing) * 2, button_width, button_height)
            
            # Draw buttons before applying hover effect
            pygame.draw.rect(screen, DARK_BLUE, host_rect, border_radius=8)
            pygame.draw.rect(screen, DARK_BLUE, join_rect, border_radius=8)
            pygame.draw.rect(screen, DARK_BLUE, rules_rect, border_radius=8)
            
            host_text = font.render("Crear partida", True, TEXT_COLOR)
            join_text = font.render("Unirse a partida", True, TEXT_COLOR)
            rules_text = font.render("Reglas", True, TEXT_COLOR)
            
            screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))
            screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
            screen.blit(rules_text, (rules_rect.centerx - rules_text.get_width() // 2, rules_rect.centery - rules_text.get_height() // 2))
            
            pygame.display.flip()
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if showing_rules:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_button_rect.collidepoint(event.pos):
                        showing_rules = False
                        scroll_offset = 0 
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing_rules = False
                        scroll_offset = 0
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset -= event.y * scroll_speed
                    # Asegurarse de que el scroll_offset no exceda el máximo o sea menor que 0
                    max_scroll = max(0, rules_total_rendered_height - rules_display_area_height)
                    scroll_offset = max(0, min(scroll_offset, max_scroll))

            elif input_active:
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if host_rect.collidepoint(event.pos):
                        network_mode = "host"
                    elif join_rect.collidepoint(event.pos):
                        input_active = True
                    elif rules_rect.collidepoint(event.pos):
                        showing_rules = True
                # Efecto hover para los botones del menú principal
                mouse_pos = pygame.mouse.get_pos()
                
                # Redibujar botones con efecto hover
                if host_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, LIGHT_BLUE, host_rect, border_radius=8)
                else:
                    pygame.draw.rect(screen, DARK_BLUE, host_rect, border_radius=8)
                host_text = font.render("Crear partida", True, TEXT_COLOR)
                screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))

                if join_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, LIGHT_BLUE, join_rect, border_radius=8)
                else:
                    pygame.draw.rect(screen, DARK_BLUE, join_rect, border_radius=8)
                join_text = font.render("Unirse a partida", True, TEXT_COLOR)
                screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))

                if rules_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, LIGHT_BLUE, rules_rect, border_radius=8)
                else:
                    pygame.draw.rect(screen, DARK_BLUE, rules_rect, border_radius=8)
                rules_text = font.render("Reglas", True, TEXT_COLOR)
                screen.blit(rules_text, (rules_rect.centerx - rules_text.get_width() // 2, rules_rect.centery - rules_text.get_height() // 2))


    # Inicializar red
    try:
        from network import Network
        network = Network(network_mode, ip_address, port)
    except Exception as e:
        print(f"Error al inicializar la red: {e}")
        traceback.print_exc()
        error_text = font.render(f"Error de inicialización: {str(e)[:50]}", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main() # Llama a main() para reiniciar desde el menú principal
        return
    
    # Si no se pudo conectar y es cliente, volver al menú principal
    if network_mode == "join" and not network.connected:
        error_text = font.render("Error de conexión. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main() # Llama a main() para reiniciar desde el menú principal
        return
    
    # Esperar a que todos los jugadores se conecten si es host
    if network_mode == "host":
        waiting = True
        player_count = 1
        
        while waiting:
            screen.fill(BG_COLOR)
            
            player_count = network.get_player_count() # Obtener el conteo más reciente
            
            wait_text = font.render(f"Esperando jugadores... ({player_count}/13)", True, TEXT_COLOR)
            screen.blit(wait_text, (SCREEN_WIDTH // 2 - wait_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            
            ip_info = font.render(f"Los jugadores pueden conectarse a:", True, TEXT_COLOR)
            screen.blit(ip_info, (SCREEN_WIDTH // 2 - ip_info.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            ip_text = font.render(f"{local_ip}:{DEFAULT_PORT} o 127.0.0.1:{DEFAULT_PORT} (local)", True, TEXT_COLOR)
            screen.blit(ip_text, (SCREEN_WIDTH // 2 - ip_text.get_width() // 2, SCREEN_HEIGHT // 2 - 75))
            
            start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
            pygame.draw.rect(screen, DARK_BLUE if player_count >= 2 else DISABLED_BUTTON_COLOR, start_rect, border_radius=5)
            start_text = font.render("Iniciar juego", True, TEXT_COLOR)
            screen.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height() // 2))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_rect.collidepoint(event.pos) and player_count >= 2:
                        waiting = False
                        network.start_game()
            clock.tick(FPS) # Mantener la tasa de refresco
 
    # Inicializar juego
    try:
        from game import Game
        from ui import UI
        game = Game(network)
        import os

        try:
            font_path = os.path.join("DejaVuSans.ttf") 
            card_font = pygame.font.Font(font_path, 32)
        except:
            card_font = pygame.font.SysFont("dejavusans", 32)
            
        ui = UI(screen, card_font=card_font)
        if network.is_host():
            if hasattr(game, "cards_to_deal"):
                ui.animate_deal(game)
                for player, cards in zip(game.players, game.cards_to_deal):
                    player.add_to_hand(cards)
                del game.cards_to_deal
                network.send_game_state(game.to_dict())
            network.game_action_handler = game.handle_network_action
    except Exception as e:
        print(f"Error al inicializar el juego: {e}")
        traceback.print_exc()
        error_text = font.render(f"Error de inicialización del juego: {str(e)[:50]}", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main() # Llama a main() para reiniciar desde el menú principal
        return
    
    # Esperar a que el juego se inicialice completamente
    waiting_for_init = True
    wait_start_time = time.time()
    timeout = 30
    
    while waiting_for_init and network.connected and time.time() - wait_start_time < timeout:
        screen.fill(BG_COLOR)
        # Asegúrate de usar la fuente 'font' que ya tienes definida en 'main'
        # No redefinir pygame.font.SysFont(None, 32) aquí, ya está arriba.
        wait_text = font.render("Esperando inicialización del juego...", True, TEXT_COLOR)
        screen.blit(wait_text, (SCREEN_WIDTH // 2 - wait_text.get_width() // 2, SCREEN_HEIGHT // 2))
        
        time_left = int(timeout - (time.time() - wait_start_time))
        time_text = font.render(f"Tiempo restante: {time_left} segundos", True, TEXT_COLOR)
        screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        
        conn_text = font.render(f"Conectado: {'Sí' if network.connected else 'No'}", True, TEXT_COLOR)
        screen.blit(conn_text, (SCREEN_WIDTH // 2 - conn_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))
        
        debug_text = font.render(f"ID del jugador: {network.id}, Modo: {network.mode}", True, TEXT_COLOR)
        screen.blit(debug_text, (SCREEN_WIDTH // 2 - debug_text.get_width() // 2, SCREEN_HEIGHT // 2 + 120))
        
        pygame.display.flip()
        
        game_state = network.receive_game_state()
        if game_state is not None:
            print("Estado del juego recibido, iniciando juego...")
            game.update_from_dict(game_state)
            waiting_for_init = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        pygame.time.delay(100) # Pequeña demora para no saturar la CPU
    
    if waiting_for_init:
        error_text = font.render("Tiempo de espera agotado para la inicialización del juego. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main() # Llama a main() para reiniciar desde el menú principal
        return
    
    # Bucle principal del juego
    running = True
    showing_round_scores = False
    last_game_state = None

    while running and network.connected:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if showing_round_scores:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    if network.is_host():
                        showing_round_scores = False
                        game.start_new_round()
                        network.send_game_state(game.to_dict())
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                ui.handle_click(event.pos, game)
            game.handle_event(event)

        if not network.is_host():
            game_state = network.receive_game_state()
            if game_state:
                game.update_from_dict(game_state)
        
        if game.state != last_game_state:
            if game.state == GAME_STATE_ROUND_END and not showing_round_scores:
                showing_round_scores = True
                print(f"Mostrando pantalla de puntuación. Host: {network.is_host()}")
            elif game.state == GAME_STATE_PLAYING and showing_round_scores:
                showing_round_scores = False
                print("Ocultando pantalla de puntuación, nueva ronda iniciada")
            last_game_state = game.state

        if showing_round_scores:
            ui.draw_round_scores(game)
            pygame.display.flip()
            continue
            
        game.update()
        screen.fill(BG_COLOR)
        ui.draw(game)
        pygame.display.flip()
        clock.tick(FPS)
    
    if not network.connected:
        error_text = font.render("Conexión perdida. Volviendo al menú principal...", True, (255, 0, 0))
        screen.fill(BG_COLOR)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        time.sleep(3)
        main() # Llama a main() para reiniciar desde el menú principal
        return
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()