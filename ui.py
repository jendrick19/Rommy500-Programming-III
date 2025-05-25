import pygame
import math
from constants import *

class UI:
    def __init__(self, screen, card_font=None):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 36)
        self.card_font = card_font or pygame.font.SysFont(None, 32)
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
        info_x = SCREEN_WIDTH - 250  # Ajustable: separa del borde derecho
        info_y = base_y

        if trios:
            trio_text = self.font.render(f"Tríos: {len(trios)}", True, (0, 100, 255))  # Azul fuerte
            self.screen.blit(trio_text, (info_x, info_y + 10))

        if seguidillas:
            seq_text = self.font.render(f"Seguidillas: {len(seguidillas)}", True, (0, 200, 200))  # Cian
            self.screen.blit(seq_text, (info_x, info_y + 35))


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
            
            # Destacar carta seleccionada
            if i == self.selected_card:
                pygame.draw.rect(self.screen, (255, 255, 0), 
                                (card_x - 5, card_y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10), 3, border_radius=5)
            
            # Resaltar en azul si está en un trío o seguidilla
            if card in cards_in_combos:
                pygame.draw.rect(self.screen, (0, 100, 255),  # Azul
                    (card_x - 3, card_y - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6), 3, border_radius=5)

            self.draw_card(card, card_x, card_y)
    
    def draw_card(self, card, x, y):
        """Dibuja una carta"""
        # Colores base
        card_color = (255, 255, 255)  # Blanco para cartas normales
        text_color = (0, 0, 0)
        if card.is_joker:
            card_color = (200, 200, 0)  # Amarillo para Jokers
        elif card.suit in ['♥', '♦']:
            card_color = (255, 200, 200)  # Rojo claro
            text_color = (150, 0, 0)      # Rojo oscuro para texto
    
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
        # Dibujar rectángulo de la carta
        card_color = (255, 255, 255)  # Blanco para cartas normales
        if card.is_joker:
            card_color = (200, 200, 0)  # Amarillo para Jokers
        elif card.suit in ['♥', '♦']:
            card_color = (255, 200, 200)  # Rojo claro para corazones y diamantes
        
        mini_width = 15
        mini_height = 20
        card_rect = pygame.Rect(x, y, mini_width, mini_height)
        pygame.draw.rect(self.screen, card_color, card_rect, border_radius=2)
        pygame.draw.rect(self.screen, (0, 0, 0), card_rect, 1, border_radius=2)
        
        # Dibujar texto miniatura
        mini_font = pygame.font.SysFont(None, 12)
        if card.is_joker:
            mini_text = mini_font.render("J", True, (0, 0, 0))
        else:
            mini_text = mini_font.render(card.value[0], True, (0, 0, 0))
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
        if not player.has_laid_down and (player.took_discard or player.took_penalty):
            lay_down_rect = pygame.Rect(start_x, start_y + (button_height + button_spacing) * 2, button_width, button_height)
            can_lay_down = player.can_lay_down(game.round_num)
            button_color = BUTTON_COLOR if can_lay_down else DISABLED_BUTTON_COLOR
            pygame.draw.rect(self.screen, button_color, lay_down_rect, border_radius=5)
            lay_down_text = self.font.render("Bajarse", True, TEXT_COLOR)
            self.screen.blit(lay_down_text, (lay_down_rect.centerx - lay_down_text.get_width() // 2, 
                                            lay_down_rect.centery - lay_down_text.get_height() // 2))
            if can_lay_down:
                self.action_buttons.append(("lay_down", lay_down_rect))
        
        # Botón para descartar
        if (player.took_discard or player.took_penalty) and self.selected_card is not None:
            discard_rect = pygame.Rect(start_x, start_y + (button_height + button_spacing) * 3, button_width, button_height)
            pygame.draw.rect(self.screen, BUTTON_COLOR, discard_rect, border_radius=5)
            discard_text = self.font.render("Descartar", True, TEXT_COLOR)
            self.screen.blit(discard_text, (discard_rect.centerx - discard_text.get_width() // 2, 
                                            discard_rect.centery - discard_text.get_height() // 2))
            self.action_buttons.append(("discard", discard_rect))
    
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
        self.screen.blit(message_surface, (SCREEN_WIDTH // 2 - message_surface.get_width() // 2, SCREEN_HEIGHT - 90))

    
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
            
        # Verificar si se hizo clic en una carta de la mano
        player = game.players[game.player_id]
        hand_x = 20
        base_y = SCREEN_HEIGHT - 280
        hand_y = base_y + 60 
        card_spacing = min(CARD_SPACING, (SCREEN_WIDTH - 40) / max(1, len(player.hand)) - CARD_WIDTH)
        
        for i, card in enumerate(player.hand):
            card_x = hand_x + i * (CARD_WIDTH + card_spacing)
            card_y = hand_y
            card_rect = pygame.Rect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT)
            
            if card_rect.collidepoint(pos):
                self.selected_card = i
                return
    
    def handle_action(self, action, game):
        """Maneja las acciones del jugador"""
        if action == "draw_deck":
            game.take_card_from_deck()
        elif action == "draw_discard":
            game.take_card_from_discard()
        elif action == "lay_down":
            game.lay_down_combination()
        elif action == "discard" and self.selected_card is not None:
            game.discard_card(self.selected_card)
            self.selected_card = None