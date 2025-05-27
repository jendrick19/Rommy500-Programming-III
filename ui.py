import pygame
import math
from constants import *

class UI:
    def __init__(self, screen, card_font=None):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 36)
        self.card_font = card_font or pygame.font.SysFont(None, 32)
        self.info_font = pygame.font.SysFont("dejavusans", 24, bold=True)
        self.selected_card = None
        self.selected_combination = None
        self.selected_player = None
        self.action_buttons = []
    
    def draw(self, game):
        """Dibuja la interfaz del juego"""
        self.screen.fill(BG_COLOR)
        
        # Verificar que el juego tiene jugadores
        if not game.players:
            error_text = self.title_font.render("Error: No hay jugadores en el juego", True, (255, 0, 0))
            self.screen.blit(error_text, (20, 20))
            return
        
        # Dibujar información de la ronda
        round_text = f"Ronda {game.round_num + 1}: {ROUNDS[game.round_num]}"
        round_surface = self.title_font.render(round_text, True, TEXT_COLOR)
        self.screen.blit(round_surface, (20, 20))
        
        # Dibujar mazo y descarte
        self.draw_deck(game, 20, 70)
        self.draw_discard_pile(game, 120, 70)
        
        # Dibujar jugadores
        self.draw_players(game)
        
        # Dibujar mano del jugador local
        self.draw_player_hand(game)
        
        # Dibujar botones de acción
        self.draw_action_buttons(game)
        
        # Dibujar mensaje de estado
        self.draw_status_message(game)
    
        # Si la ronda terminó, mostrar tabla de puntuaciones y botón
        if game.state == GAME_STATE_ROUND_END:
            self.draw_score_table(game)
            return
    
    def draw_deck(self, game, x, y):
        """Dibuja el mazo"""
        # Dibujar rectángulo para el mazo
        deck_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_BACK_COLOR, deck_rect, border_radius=5)
        pygame.draw.rect(self.screen, TEXT_COLOR, deck_rect, 2, border_radius=5)
        
        # Dibujar texto
        deck_text = self.font.render(f"Mazo ({len(game.deck.cards)})", True, TEXT_COLOR)
        self.screen.blit(deck_text, (x, y + CARD_HEIGHT + 5))
    
    def draw_discard_pile(self, game, x, y):
        """Dibuja el montón de descarte"""
        # Dibujar rectángulo para el descarte
        discard_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, BG_COLOR, discard_rect, border_radius=5)
        pygame.draw.rect(self.screen, TEXT_COLOR, discard_rect, 2, border_radius=5)
        
        # Dibujar la carta superior si hay alguna
        if game.discard_pile.cards:
            top_card = game.discard_pile.peek()
            self.draw_card(top_card, x, y)
        
        # Dibujar texto
        discard_text = self.font.render(f"Descarte ({len(game.discard_pile.cards)})", True, TEXT_COLOR)
        self.screen.blit(discard_text, (x, y + CARD_HEIGHT + 5))
    
    def draw_players(self, game):
        """Dibuja información de todos los jugadores"""
        player_count = len(game.players)
        
        # Calcular posiciones
        if player_count <= 4:
            positions = [
                (SCREEN_WIDTH // 2 - 150, 50),  # Arriba
                (SCREEN_WIDTH - 250, SCREEN_HEIGHT // 2 - 100),  # Derecha
                (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 200),  # Abajo (jugador local)
                (50, SCREEN_HEIGHT // 2 - 100)  # Izquierda
            ]
        else:
            # Para más de 4 jugadores, distribuir en círculo
            positions = []
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            radius = min(center_x, center_y) - 150
            angle_step = 2 * 3.14159 / player_count
            
            for i in range(player_count):
                angle = i * angle_step
                x = center_x + radius * math.cos(angle) - 150
                y = center_y + radius * math.sin(angle) - 100
                positions.append((x, y))
        
        # Verificar que el ID del jugador es válido
        if game.player_id < 0 or game.player_id >= len(game.players):
            error_text = self.title_font.render(f"Error: ID de jugador no válido ({game.player_id})", True, (255, 0, 0))
            self.screen.blit(error_text, (20, SCREEN_HEIGHT - 180))
            return
        
        # Dibujar cada jugador (excepto el jugador local)
        local_player_idx = game.player_id
        for i, player in enumerate(game.players):
            if i == local_player_idx:
                continue  # El jugador local se dibuja separadamente
            
            pos_idx = i if i < local_player_idx else i - 1
            if pos_idx < len(positions):
                x, y = positions[pos_idx % len(positions)]
                
                # Dibujar marco del jugador actual
                if i == game.current_player_idx:
                    pygame.draw.rect(self.screen, PLAYER_COLORS[i % len(PLAYER_COLORS)], 
                                    (x - 10, y - 10, 320, 220), 3, border_radius=10)
                
                # Dibujar información del jugador
                player_text = f"Jugador {i+1}" + (" (Mano)" if player.is_mano else "")
                player_surface = self.font.render(player_text, True, PLAYER_COLORS[i % len(PLAYER_COLORS)])
                self.screen.blit(player_surface, (x, y))
                
                score_text = f"Puntos: {player.score}"
                score_surface = self.font.render(score_text, True, TEXT_COLOR)
                self.screen.blit(score_surface, (x, y + 25))
                
                cards_text = f"Cartas: {len(player.hand)}"
                cards_surface = self.font.render(cards_text, True, TEXT_COLOR)
                self.screen.blit(cards_surface, (x, y + 50))
                
                status_text = "Bajado" if player.has_laid_down else "No bajado"
                status_surface = self.font.render(status_text, True, TEXT_COLOR)
                self.screen.blit(status_surface, (x, y + 75))
                
                # Dibujar combinaciones del jugador
                self.draw_player_combinations(player, x, y + 100)
    
    def draw_player_combinations(self, player, x, y):
        """Dibuja las combinaciones de un jugador"""
        for i, combo in enumerate(player.combinations):
            combo_type = "Trío" if combo["type"] == "trio" else "Seguidilla"
            combo_text = f"{combo_type}: "
            combo_surface = self.font.render(combo_text, True, TEXT_COLOR)
            self.screen.blit(combo_surface, (x, y + i * 25))
            
            # Dibujar cartas en miniatura
            for j, card in enumerate(combo["cards"]):
                mini_x = x + 80 + j * 20
                mini_y = y + i * 25
                self.draw_mini_card(card, mini_x, mini_y)
    
    def draw_player_hand(self, game):
        """Dibuja la mano del jugador local"""
        # Verificar que el ID del jugador es válido
        if game.player_id < 0 or game.player_id >= len(game.players):
            error_text = self.title_font.render(f"Error: ID de jugador no válido ({game.player_id})", True, (255, 0, 0))
            self.screen.blit((error_text, (20, SCREEN_HEIGHT - 180)), True, (255, 0, 0))
            self.screen.blit(error_text, (20, SCREEN_HEIGHT - 180))
            return
            
        player = game.players[game.player_id]
        
        # Dibujar información del jugador
        base_y = SCREEN_HEIGHT - 280

        player_text = f"Tu mano (Jugador {game.player_id + 1})" + (" (Mano)" if player.is_mano else "")
        player_surface = self.title_font.render(player_text, True, PLAYER_COLORS[game.player_id % len(PLAYER_COLORS)])
        self.screen.blit(player_surface, (20, base_y))
        
        score_text = f"Puntos: {player.score}"
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (20, base_y + 30))
        
        status_text = "Bajado" if player.has_laid_down else "No bajado"
        status_surface = self.font.render(status_text, True, TEXT_COLOR)
        self.screen.blit(status_surface, (150, base_y + 30))

        # Mostrar trío(s) y seguidilla(s) detectados
        trios = player.detect_trios()
        seguidillas = player.detect_seguidillas()

        # Calcular posición derecha de los mensajes
        # Fuente decorativa más grande y en negrita
        info_font = pygame.font.SysFont("dejavusans", 28, bold=True)

        info_x = SCREEN_WIDTH - 240  # Más hacia el borde derecho
        info_y = base_y - 25  # CAMBIO: Subir 30 píxeles (era base_y + 5)

        if trios:
            trio_text = info_font.render(f"🃏 Tríos: {len(trios)}", True, (30, 144, 255))  # Azul brillante
            self.screen.blit(trio_text, (info_x, info_y))

        if seguidillas:
            seq_text = info_font.render(f"♠ Seguidillas: {len(seguidillas)}", True, (50, 205, 50))  # Verde lima
            # CAMBIO: Mover seguidilla más a la izquierda (restar 50 píxeles)
            self.screen.blit(seq_text, (info_x - 50, info_y + 35))

        # Dibujar cartas de la mano
        hand_x = 20
        hand_y = base_y + 60
        card_spacing = min(CARD_SPACING, (SCREEN_WIDTH - 40) / max(1, len(player.hand)) - CARD_WIDTH)

        # Obtener cartas que están en tríos o seguidillas
        trios = player.detect_trios()
        seguidillas = player.detect_seguidillas()

        # Aplanar las listas de combinaciones en una sola lista de cartas
        cards_in_combos = set()
        for combo in trios + seguidillas:
            cards_in_combos.update(combo)

        
        for i, card in enumerate(player.hand):
            card_x = hand_x + i * (CARD_WIDTH + card_spacing)
            card_y = hand_y
            # Si está seleccionada, subirla
            if i == self.selected_card:
                card_y -= 20  # Sube la carta 20 píxeles
                pygame.draw.rect(self.screen, (255, 255, 0), 
                                (card_x - 5, card_y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10), 3, border_radius=5)
            # Resaltar en azul si está en un trío o seguidilla
            if card in cards_in_combos:
                pygame.draw.rect(self.screen, (0, 100, 255),  # Azul
                    (card_x - 3, card_y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6), 3, border_radius=5)

            self.draw_card(card, card_x, card_y)
            # Dibujar combinaciones bajadas propias
        if player.has_laid_down and player.combinations:
            label_font = pygame.font.SysFont("dejavusans", 20, bold=True)
            label = label_font.render("Cartas bajadas:", True, TEXT_COLOR)
            self.screen.blit(label, (20, hand_y + CARD_HEIGHT + 20))

            combo_y = hand_y + CARD_HEIGHT + 50
            for combo in player.combinations:
                combo_text = f"{combo['type'].capitalize()}:"
                combo_label = self.font.render(combo_text, True, TEXT_COLOR)
                self.screen.blit(combo_label, (30, combo_y))

                for j, card in enumerate(combo['cards']):
                    self.draw_mini_card(card, 110 + j * 20, combo_y)
                combo_y += 30


    def draw_local_player_combinations(self, player, base_y):
        """Dibuja las combinaciones bajadas del jugador local debajo de su mano"""
        title = self.font.render("Cartas bajadas:", True, TEXT_COLOR)
        self.screen.blit(title, (20, base_y + CARD_HEIGHT + 20))
    
        for i, combo in enumerate(player.combinations):
            label = self.font.render("Trío" if combo["type"] == "trio" else "Seguidilla", True, TEXT_COLOR)
            self.screen.blit(label, (20, base_y + CARD_HEIGHT + 50 + i * 40))

            for j, card in enumerate(combo["cards"]):
                x = 120 + j * 30
                y = base_y + CARD_HEIGHT + 50 + i * 40
                self.draw_mini_card(card, x, y)

    
    def draw_card(self, card, x, y):
        """Dibuja una carta"""
        # Colores base según el palo
        if card.is_joker:
            card_color = (200, 200, 0)  # Amarillo para Jokers
            text_color = (0, 0, 0)
        elif card.suit == '♦':
            card_color = (255, 255, 100)  # Amarillo para diamantes
            text_color = (180, 140, 0)
        elif card.suit == '♣':
            card_color = (180, 220, 255)  # Azul claro para tréboles
            text_color = (0, 60, 180)
        elif card.suit == '♠':
            card_color = (220, 220, 220)  # Gris claro para picas (fondo)
            text_color = (0, 0, 0)        # Negro para texto
        elif card.suit == '♥':
            card_color = (255, 200, 200)  # Rojo claro para corazones
            text_color = (150, 0, 0)
        else:
            card_color = (255, 255, 255)
            text_color = (0, 0, 0)

    # Rectángulo principal
        card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, card_color, card_rect, border_radius=5)
        pygame.draw.rect(self.screen, (0, 0, 0), card_rect, 2, border_radius=5)

        if card.is_joker:
            # 🃏 centrado
            joker_text = self.card_font.render("🃏", True, text_color)
            self.screen.blit(
                joker_text, 
                (x + CARD_WIDTH // 2 - joker_text.get_width() // 2,
                 y + CARD_HEIGHT // 2 - joker_text.get_height() // 2)
            )
        else:
            # Esquinas
            value_text = self.card_font.render(card.value, True, text_color)
            suit_text = self.card_font.render(card.suit, True, text_color)
        
            # Superior izquierda (valor)
            self.screen.blit(value_text, (x + 5, y + 3))
            # Inferior derecha (palo)
            self.screen.blit(suit_text, (
                x + CARD_WIDTH - suit_text.get_width() - 5,
                y + CARD_HEIGHT - suit_text.get_height() - 5
            ))

    
    def draw_mini_card(self, card, x, y):
        """Dibuja una versión miniatura de una carta"""
        # Colores base según el palo
        if card.is_joker:
            card_color = (200, 200, 0)  # Amarillo para Jokers
            text_color = (0, 0, 0)
        elif card.suit == '♦':
            card_color = (255, 255, 100)  # Amarillo para diamantes
            text_color = (180, 140, 0)
        elif card.suit == '♣':
            card_color = (180, 220, 255)  # Azul claro para tréboles
            text_color = (0, 60, 180)
        elif card.suit == '♠':
            card_color = (220, 220, 220)  # Gris claro para picas (fondo)
            text_color = (0, 0, 0)
        elif card.suit == '♥':
            card_color = (255, 200, 200)  # Rojo claro para corazones
            text_color = (150, 0, 0)
        else:
            card_color = (255, 255, 255)
            text_color = (0, 0, 0)

        mini_width = 20 if len(card.value) > 1 else 15
        mini_height = 20
        card_rect = pygame.Rect(x, y, mini_width, mini_height)
        pygame.draw.rect(self.screen, card_color, card_rect, border_radius=2)
        pygame.draw.rect(self.screen, (0, 0, 0), card_rect, 1, border_radius=2)
        
        # Dibujar texto miniatura
        mini_font = pygame.font.SysFont(None, 12)
        if card.is_joker:
            mini_text = mini_font.render("J", True, text_color)
        else:
            mini_text = mini_font.render(card.value, True, text_color)
        self.screen.blit(mini_text, (x + mini_width // 2 - mini_text.get_width() // 2, 
                                    y + mini_height // 2 - mini_text.get_height() // 2))
    
    def draw_action_buttons(self, game):
        """Dibuja los botones de acción"""
        self.action_buttons = []
        
        # Verificar que el ID del jugador es válido
        if game.player_id < 0 or game.player_id >= len(game.players):
            return
            
        # Solo mostrar botones si es el turno del jugador local
        if game.current_player_idx != game.player_id:
            return
        
        player = game.players[game.player_id]
        button_width = 150
        button_height = 40
        button_spacing = 10
        start_x = SCREEN_WIDTH - button_width - 20
        start_y = 20
        
        # Botón para tomar del mazo
        if not player.took_discard and not player.took_penalty:
            draw_deck_rect = pygame.Rect(start_x, start_y, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, draw_deck_rect, border_radius=5)
            draw_deck_text = self.font.render("Tomar del mazo", True, TEXT_COLOR)
            self.screen.blit(draw_deck_text, (draw_deck_rect.centerx - draw_deck_text.get_width() // 2, 
                                            draw_deck_rect.centery - draw_deck_text.get_height() // 2))
            self.action_buttons.append(("draw_deck", draw_deck_rect))
            
            # Botón para tomar del descarte
            draw_discard_rect = pygame.Rect(start_x, start_y + button_height + button_spacing, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, draw_discard_rect, border_radius=5)
            draw_discard_text = self.font.render("Tomar del descarte", True, TEXT_COLOR)
            self.screen.blit(draw_discard_text, (draw_discard_rect.centerx - draw_discard_text.get_width() // 2, 
                                                draw_discard_rect.centery - draw_discard_text.get_height() // 2))
            self.action_buttons.append(("draw_discard", draw_discard_rect))
        
        # Botón para bajarse
        show_lay_down = False
        if (player.took_discard or player.took_penalty):
            if game.round_num == 0:
                # En ronda 1, permitir bajarse si puede (aunque ya haya bajado una vez)
                if player.can_lay_down(game.round_num):
                    show_lay_down = True
            else:
                # En otras rondas, solo si no se ha bajado aún
                if not player.has_laid_down and player.can_lay_down(game.round_num):
                    show_lay_down = True

        if show_lay_down:
            lay_down_rect = pygame.Rect(start_x, start_y + (button_height + button_spacing) * 2, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, lay_down_rect, border_radius=5)
            lay_down_text = self.font.render("Bajarse", True, TEXT_COLOR)
            self.screen.blit(lay_down_text, (lay_down_rect.centerx - lay_down_text.get_width() // 2, 
                                            lay_down_rect.centery - lay_down_text.get_height() // 2))
            self.action_buttons.append(("lay_down", lay_down_rect))
        
        # Botón para descartar
        if (player.took_discard or player.took_penalty) and self.selected_card is not None:
            discard_rect = pygame.Rect(start_x, start_y + (button_height + button_spacing) * 3, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, discard_rect, border_radius=5)
            discard_text = self.font.render("Descartar", True, TEXT_COLOR)
            self.screen.blit(discard_text, (discard_rect.centerx - discard_text.get_width() // 2, 
                                            discard_rect.centery - discard_text.get_height() // 2))
            self.action_buttons.append(("discard", discard_rect))
        # Botón para añadir a combinación
        if (player.took_discard or player.took_penalty) and self.selected_card is not None and self.selected_combination is not None:
            add_to_combination_rect = pygame.Rect(start_x, start_y + (button_height + button_spacing) * 4, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, add_to_combination_rect, border_radius=5)
            add_to_combination_text = self.font.render("Añadir a la combinación", True, TEXT_COLOR)
            self.screen.blit(add_to_combination_text, (add_to_combination_rect.centerx - add_to_combination_text.get_width() // 2,add_to_combination_rect.centery - add_to_combination_text.get_height() // 2))
    
    def draw_status_message(self, game):
        """Dibuja un mensaje de estado"""
        message = ""
        
        if game.state == GAME_STATE_WAITING:
            message = "Esperando a que todos los jugadores se conecten..."
        elif game.state == GAME_STATE_ROUND_END:
            message = "¡Fin de la ronda! Esperando a que comience la siguiente ronda..."
        elif game.state == GAME_STATE_GAME_END:
            if game.winner and game.winner.id == game.player_id:
                message = "¡Has ganado el juego!"
            else:
                winner_name = f"Jugador {game.winner.id + 1}" if game.winner else "Desconocido"
                message = f"Fin del juego. Ganador: {winner_name}"
        elif game.current_player_idx == game.player_id:
            message = "Es tu turno"
        else:
            current_player = game.players[game.current_player_idx]
            message = f"Turno del Jugador {game.current_player_idx + 1}"
        
        message_surface = self.title_font.render(message, True, TEXT_COLOR)
        self.screen.blit(message_surface, (SCREEN_WIDTH // 2 - message_surface.get_width() // 2, SCREEN_HEIGHT - 50))

    
    def handle_click(self, pos, game):
        """Maneja los clics del ratón"""
        # Verificar si se hizo clic en un botón de acción
        for action, rect in self.action_buttons:
            if rect.collidepoint(pos):
                self.handle_action(action, game)
                return

        # Verificar que el ID del jugador es válido
        if game.player_id < 0 or game.player_id >= len(game.players):
            return

        # Selección de carta de la mano del jugador local
        player = game.players[game.player_id]
        hand_x = 20
        base_y = SCREEN_HEIGHT - 280
        hand_y = base_y + 60
        card_spacing = min(CARD_SPACING, (SCREEN_WIDTH - 40) / max(1, len(player.hand)) - CARD_WIDTH)

        for i in range(len(player.hand)):
            card_x = hand_x + i * (CARD_WIDTH + card_spacing)
            card_y = hand_y
            card_rect = pygame.Rect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                self.selected_card = i
                # Si ya hay una combinación seleccionada, intentar añadir la carta
                if self.selected_combination is not None and self.selected_player is not None:
                    self.handle_action("add_to_combo", game)
                return

        # Selección de combinaciones de cualquier jugador
        for pid, p in enumerate(game.players):
            for cidx in range(len(p.combinations)):
                combo_rect = self.get_combination_rect(pid, cidx, game)
                if combo_rect.collidepoint(pos):
                    self.selected_combination = cidx
                    self.selected_player = pid
                    if self.selected_card is not None:
                        self.handle_action("add_to_combo", game)
                    return

        # Si no se hizo clic en nada relevante, limpiar selección
        self.selected_card = None
        self.selected_combination = None
        self.selected_player = None

    def handle_action(self, action, game):
        if action == "draw_deck":
            game.take_card_from_deck()
            game.update()
        elif action == "draw_discard":
            game.take_card_from_discard()
            game.update()
        elif action == "lay_down":
            game.lay_down_combination()
            game.update()
        elif action == "discard" and self.selected_card is not None:
            game.discard_card(self.selected_card)
            self.selected_card = None
            game.update()
        elif action == "next_round":
            if game.network.is_host():
                game.start_new_round()
                game.update()
        elif action == "add_to_combo" and self.selected_card is not None and self.selected_combination is not None and self.selected_player is not None:
            # Permitir añadir a cualquier combinación bajada (propia o de otro jugador)
            game.add_to_combination(
                self.selected_card,
                self.selected_combination,
                self.selected_player
            )
            # No limpiar self.selected_combination ni self.selected_player,
            # solo limpiar la carta seleccionada para permitir añadir varias seguidas
            self.selected_card = None
        game.update()

    def draw_score_table(self, game):
        # Fondo semitransparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((30, 30, 30))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("Fin de la ronda", True, (255, 255, 0))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        # Tabla de puntuaciones
        font = pygame.font.SysFont(None, 36)
        y = 180
        for player in sorted(game.players, key=lambda p: -p.score):
            text = font.render(f"{player.name}: {player.score} puntos", True, (255, 255, 255))
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 50

        # Botón para continuar
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, y + 40, 200, 50)
        pygame.draw.rect(self.screen, BUTTON_COLOR, button_rect, border_radius=8)
        btn_text = font.render("Siguiente ronda", True, (255, 255, 255))
        self.screen.blit(btn_text, (button_rect.centerx - btn_text.get_width() // 2, button_rect.centery - btn_text.get_height() // 2))
        self.action_buttons = [("next_round", button_rect)]

    def animate_deal(self, game):
        """Animación de reparto de cartas a todos los jugadores antes de que aparezcan en la mano"""
        num_cards = 10
        # Prepara manos temporales vacías para la animación
        temp_hands = [[] for _ in game.players]
        for card_num in range(num_cards):
            for pid, player in enumerate(game.players):
                # Calcula posición destino (mano del jugador)
                if pid == game.player_id:
                    dest_x = 20 + card_num * (CARD_WIDTH + 5)
                    dest_y = SCREEN_HEIGHT - 220
                else:
                    # Puedes ajustar estas posiciones para otros jugadores
                    dest_x = 100 + pid * 120
                    dest_y = 100

                # Animar carta desde el mazo
                for t in range(0, 21):
                    self.screen.fill(BG_COLOR)
                    # Dibuja el estado actual del juego SIN cartas en la mano real,
                    # pero con las cartas ya animadas en temp_hands
                    self.draw_deal_state(game, temp_hands)
                    # Interpolación lineal desde el mazo (20,70)
                    x = 20 + (dest_x - 20) * t // 20
                    y = 70 + (dest_y - 70) * t // 20
                    # Dibuja la carta en movimiento (boca abajo para todos)
                    pygame.draw.rect(self.screen, CARD_BACK_COLOR, (x, y, CARD_WIDTH, CARD_HEIGHT), border_radius=5)
                    pygame.draw.rect(self.screen, (0, 0, 0), (x, y, CARD_WIDTH, CARD_HEIGHT), 2, border_radius=5)
                    pygame.display.flip()
                    pygame.time.delay(12)

                # Al terminar la animación, añade la carta a la mano temporal y muestra la carta (boca arriba solo para el jugador local)
                card = game.cards_to_deal[pid][card_num]
                temp_hands[pid].append(card)
                self.screen.fill(BG_COLOR)
                self.draw_deal_state(game, temp_hands, reveal_last_for_player=pid)
                pygame.display.flip()
                pygame.time.delay(80)

        # Redibuja el estado final (las cartas aparecerán después en la mano real)
        self.draw(game)
        pygame.display.flip()

    def draw_deal_state(self, game, temp_hands, reveal_last_for_player=None):
        """Dibuja el estado del juego durante el reparto, usando manos temporales"""
        # Mazo y descarte
        self.draw_deck(game, 20, 70)
        self.draw_discard_pile(game, 120, 70)
        # Jugadores (solo muestra backs para otros jugadores)
        for pid, player in enumerate(game.players):
            if pid == game.player_id:
                # Mano local: muestra cartas boca arriba, pero solo las de temp_hands
                hand = temp_hands[pid]
                hand_x = 20
                hand_y = SCREEN_HEIGHT - 220
                card_spacing = min(CARD_SPACING, (SCREEN_WIDTH - 40) / max(1, len(hand)) - CARD_WIDTH)
                for i, card in enumerate(hand):
                    card_x = hand_x + i * (CARD_WIDTH + card_spacing)
                    card_y = hand_y
                    # Si es la última carta y reveal_last_for_player==pid, mostrar boca arriba
                    if reveal_last_for_player == pid and i == len(hand) - 1:
                        self.draw_card(card, card_x, card_y)
                    else:
                        # Mostrar boca abajo
                        pygame.draw.rect(self.screen, CARD_BACK_COLOR, (card_x, card_y, CARD_WIDTH, CARD_HEIGHT), border_radius=5)
                        pygame.draw.rect(self.screen, (0, 0, 0), (card_x, card_y, CARD_WIDTH, CARD_HEIGHT), 2, border_radius=5)
            else:
                # Otros jugadores: solo backs
                hand = temp_hands[pid]
                hand_x = 100 + pid * 120
                hand_y = 100
                for i in range(len(hand)):
                    card_x = hand_x + i * 10
                    card_y = hand_y
                    pygame.draw.rect(self.screen, CARD_BACK_COLOR, (card_x, card_y, CARD_WIDTH, CARD_HEIGHT), border_radius=5)
                    pygame.draw.rect(self.screen, (0, 0, 0), (card_x, card_y, CARD_WIDTH, CARD_HEIGHT), 2, border_radius=5)
    def animate_card_move(self, start_pos, end_pos, card):
        """Animación de movimiento de una carta"""
        for t in range(0, 21):
            self.screen.fill(BG_COLOR)
            # Dibuja el estado actual del juego (sin la carta en movimiento)
            # ... (puedes llamar a self.draw(game) si no interfiere)
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * t // 20
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * t // 20
            self.draw_card(card, x, y)
            pygame.display.flip()
            pygame.time.delay(10)

    def get_combination_rect(self, pid, cidx, game):
        """Devuelve el rectángulo de la combinación cidx del jugador pid"""
        player_count = len(game.players)
        if player_count <= 4:
            # Usa las posiciones del arreglo positions en draw_players
            positions = [
                (SCREEN_WIDTH // 2 - 150, 50),  # Arriba
                (SCREEN_WIDTH - 250, SCREEN_HEIGHT // 2 - 100),  # Derecha
                (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 200),  # Abajo (jugador local)
                (50, SCREEN_HEIGHT // 2 - 100)  # Izquierda
            ]
            local_player_idx = game.player_id
            pos_idx = pid if pid < local_player_idx else pid - 1 if pid > local_player_idx else None
            if pos_idx is not None and pos_idx < len(positions):
                x, y = positions[pos_idx]
                return pygame.Rect(x + 80, y + 100 + cidx * 25, 120, 25)
        else:
            # Para más de 4 jugadores, distribuye en círculo alrededor del centro
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            radius = min(center_x, center_y) - 180
            angle_step = 2 * math.pi / player_count
            angle = pid * angle_step
            # Calcula la posición base del jugador
            base_x = center_x + radius * math.cos(angle)
            base_y = center_y + radius * math.sin(angle)
            # Ajusta para dejar espacio para combinaciones
            combo_x = int(base_x) + 80
            combo_y = int(base_y) + 40 + cidx * 28
            return pygame.Rect(combo_x, combo_y, 120, 25)
        # Fallback
        return pygame.Rect(100 + pid * 200, 150 + cidx * 30, 120, 25)

    def draw_round_scores(self, game):
        self.screen.fill(BG_COLOR)
        title = self.font.render("Fin de la ronda", True, (255, 255, 0))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        y = 160
        for idx, player in enumerate(game.players):
            name = getattr(player, "name", f"Jugador {idx+1}")
            score = game.round_scores[idx] if hasattr(game, "round_scores") and idx < len(game.round_scores) else 0
            text = self.font.render(f"{name}: {score} puntos", True, TEXT_COLOR)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 40
        # Mostrar ganador solo si existe
        if hasattr(game, "round_winner") and game.round_winner is not None and 0 <= game.round_winner < len(game.players):
            winner_name = getattr(game.players[game.round_winner], "name", f"Jugador {game.round_winner+1}")
            winner_text = self.font.render(f"Ganador de la ronda: {winner_name}", True, (0, 255, 0))
            self.screen.blit(winner_text, (SCREEN_WIDTH // 2 - winner_text.get_width() // 2, y + 20))
        continue_text = self.font.render("Haz clic para continuar...", True, (200, 200, 200))
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, y + 70))