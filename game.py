import random
import pygame
import traceback
import time
from constants import *
from card import Card, Deck, DiscardPile
from player import Player

class Game:
    def __init__(self, network):
        self.network = network
        self.players = []
        num_players = network.get_player_count()
        num_decks = max(1, (num_players + 2) // 3)  # 1 mazo por cada 3 jugadores
        self.deck = Deck(num_decks=num_decks)
        self.discard_pile = DiscardPile()
        self.current_player_idx = 0
        self.round_num = 0
        self.state = GAME_STATE_WAITING
        self.winner = None
        self.deck_checked = False
        self.eliminated_players = []
        self.player_id = network.get_id()  # ID del jugador local
        self.round_scores = [0 for _ in range(13)]  # Máximo 13 jugadores
        self.round_winner = None
        
        # Inicializar el juego si somos el host
        if network.is_host():
            self.initialize_game()
        else:
            # Si no somos host, esperar a recibir el estado del juego
            print(f"Cliente inicializado con ID {self.player_id}, esperando estado del juego...")
    
    def initialize_game(self):
        """Inicializa el juego (solo el host)"""
        try:
            # Crear jugadores
            player_count = self.network.get_player_count()
            for i in range(player_count):
                player = Player(i, f"Jugador {i+1}")
                self.players.append(player)
            
            # Designar el primer "mano"
            self.players[0].is_mano = True
            
            # Repartir cartas
            
            if not self.deck_checked:
                self.check_deck_duplicates("Inicio juego → ")
                self.deck_checked = True

            # Preparar cartas a repartir
            cards_to_deal = []
            for player in self.players:
                cards = self.deck.deal(10)
                cards_to_deal.append(cards)
            # No las añadas aún a la mano

            # Colocar la primera carta en el descarte
            self.discard_pile.add(self.deck.deal())
            
            # Establecer el estado del juego
            self.state = GAME_STATE_PLAYING
            
            # Enviar el estado inicial a todos los jugadores
            self.network.send_game_state(self.to_dict())
            print("Estado inicial del juego enviado a todos los jugadores")
            
            # Guardar temporalmente las cartas a repartir para la animación
            self.cards_to_deal = cards_to_deal
        except Exception as e:
            print(f"Error al inicializar el juego: {e}")
            traceback.print_exc()
    
    def handle_event(self, event):
        """Maneja eventos de pygame"""
        if self.state != GAME_STATE_PLAYING:
            return
        
        # Solo procesar eventos si es el turno del jugador local
        if self.current_player_idx != self.player_id:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == GAME_STATE_ROUND_END and self.network.is_host():
                self.start_new_round()
            # Aquí se manejarían los clics del ratón para las acciones del juego
            # Como tomar cartas, jugar combinaciones, etc.
            pass
    
    def update(self):
        """Actualiza el estado del juego"""
        game_state = None
            # Recibe el estado del juego desde la red (si no eres host)
        if not self.network.is_host():
            game_state = self.network.receive_game_state()
        
        if game_state:
            self.update_from_dict(game_state)
            try:
                # Asegurarse de que el player_id sigue siendo válido
                if self.player_id >= len(self.players):
                    print(f"Error: player_id {self.player_id} fuera de rango. Ajustando...")
                    self.player_id = min(self.player_id, len(self.players) - 1)
            except Exception as e:
                print(f"Error al actualizar el estado del juego: {e}")
                traceback.print_exc()
        
        # Verificar si el juego ha terminado
        if self.state == GAME_STATE_GAME_END:
            return
        
        # Verificar si la ronda ha terminado
        if self.state == GAME_STATE_ROUND_END:
            # Iniciar nueva ronda si somos el host
            if self.network.is_host():
                self.end_round()
            return
    
    def start_new_round(self):
        """Inicia una nueva ronda (solo el host)"""
        # Incrementar el número de ronda
        self.round_num = (self.round_num + 1) % len(ROUNDS)
        
        # Reiniciar el mazo y el descarte
        self.deck.reset()
        self.deck_checked = False  # Para volver a permitir validación
        self.check_deck_duplicates(f"Ronda {self.round_num + 1} → ")
        self.discard_pile = DiscardPile()
        self.sequences_laid_down = 0
        self.trios_laid_down = 0
        
        # Reiniciar los jugadores
        for player in self.players:
            player.has_laid_down_trio = False
            player.has_laid_down_sequence = False
            player.sequences_laid_down = 0
            player.trios_laid_down = 0
            player.hand = []
            player.combinations = []
            player.has_laid_down = False
            player.took_discard = False
            player.took_penalty = False
            player.has_completed_round_requirement = False  # Reset round requirement
        
        # Designar el nuevo "mano" (el ganador de la ronda anterior)
        for i, player in enumerate(self.players):
            player.is_mano = (i == self.current_player_idx)
        
        # Repartir cartas
        for player in self.players:
            player.add_to_hand(self.deck.deal(10))
        
        # Colocar la primera carta en el descarte
        self.discard_pile.add(self.deck.deal())
        
        # Establecer el estado del juego
        self.state = GAME_STATE_PLAYING
        
        # Enviar el estado actualizado a todos los jugadores
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
    
    def take_card_from_deck(self):
        """El jugador actual toma una carta del mazo"""
        if self.state != GAME_STATE_PLAYING:
            return False
        
        player = self.players[self.current_player_idx]
        
        # Verificar si el jugador ya tomó una carta
        if player.took_discard or player.took_penalty:
            return False
        
        # Tomar una carta del mazo
        card = self.deck.deal()
        if not card:
            # Si el mazo está vacío, mezclar el descarte (excepto la carta superior)
            if len(self.discard_pile.cards) <= 1:
                return False
            
            top_card = self.discard_pile.take()
            self.deck.cards = self.discard_pile.cards
            self.discard_pile.cards = []
            if top_card:
                self.discard_pile.add(top_card)
            self.deck.shuffle()
            
            # Intentar de nuevo
            card = self.deck.deal()
            if not card:
                return False
        
        player.add_to_hand(card)
        player.took_penalty = True  # Marcar que el jugador tomó una carta
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_DRAW_DECK,
                'player_id': self.player_id
            })
        
        return True
    
    def take_card_from_discard(self, is_penalty=False):
        """El jugador actual toma una carta del descarte"""
        if self.state != GAME_STATE_PLAYING:
            return False
        
        player = self.players[self.current_player_idx]
        
        # Verificar si el jugador ya tomó una carta
        if player.took_discard or player.took_penalty:
            return False
        
        # Verificar si hay cartas en el descarte
        if len(self.discard_pile.cards) == 0:
            return False
        
        # Tomar la carta superior del descarte
        card = self.discard_pile.take()
        if not card:
            return False
        
        player.add_to_hand(card)
        
        if is_penalty:
            player.took_penalty = True
            # Tomar una carta adicional del mazo como penalización
            penalty_card = self.deck.deal()
            if penalty_card:
                player.add_to_hand(penalty_card)
        else:
            player.took_discard = True
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_DRAW_DISCARD,
                'player_id': self.player_id,
                'is_penalty': is_penalty
            })
        
        return True
    
    def lay_down_combination(self):
        """El jugador actual baja sus combinaciones"""
        if self.state != GAME_STATE_PLAYING:
            return False

        player = self.players[self.current_player_idx]

        # Solo bloquear en ronda 4 (donde debe bajarse todo junto)
        if self.round_num == 3 and player.has_laid_down:
            return False

        # Verificar si el jugador puede bajarse
        if not player.can_lay_down(self.round_num):
            return False

        # Bajar las combinaciones
        if not player.lay_down(self.round_num):
            return False

        # Verificar si el jugador ha ganado la ronda después de bajarse
        if self.check_round_win_condition(player):
            self.end_round(winner_idx=self.current_player_idx)
            return True
        else:
            # Enviar el estado actualizado
            if self.network.is_host():
                self.network.send_game_state(self.to_dict())
            else:
                self.network.send_action({
                    'type': ACTION_PLAY_COMBINATION,
                    'player_id': self.player_id
                })
        return True
    
    def add_to_combination(self, card_idx, combination_idx, player_idx=None, actor_idx=None):
        print(f"[DEBUG] add_to_combination llamado con card_idx={card_idx}, combination_idx={combination_idx}, player_idx={player_idx}")

        if actor_idx is None:
            actor_idx = self.player_id
        local_player = self.players[actor_idx]
        target_player = self.players[player_idx if player_idx is not None else actor_idx]
        target_player_idx = player_idx if player_idx is not None else actor_idx

        print(f"[DEBUG] local_player.id={local_player.id}, target_player.id={target_player.id}, target_player_idx={target_player_idx}")
        print(f"[DEBUG] Mano del jugador local antes: {[str(c) for c in local_player.hand]}")
        print(f"[DEBUG] Combinaciones del jugador objetivo antes: {[[str(c) for c in combo['cards']] for combo in target_player.combinations]}")

        # Validar índices
        if card_idx < 0 or card_idx >= len(local_player.hand):
            print(f"[ERROR] Índice de carta inválido: {card_idx} para mano de tamaño {len(local_player.hand)}")
            return False
        if combination_idx < 0 or combination_idx >= len(target_player.combinations):
            print(f"[ERROR] Índice de combinación inválido: {combination_idx} para combinaciones de tamaño {len(target_player.combinations)}")
            return False

        card = local_player.hand[card_idx]
        print(f"[DEBUG] Intentando agregar carta: {card} a combinación {combination_idx} del jugador {target_player.id}")

        # Validar si la carta puede agregarse usando la función central
        can_add = self.can_add_to_combination(card, combination_idx, target_player_idx)
        print(f"[DEBUG] Resultado de can_add_to_combination: {can_add}")
        if not can_add:
            print(f"[INFO] No se puede agregar {card} a combinación {combination_idx} del jugador {target_player.id}")
            return False

        replaced_joker = False
        if target_player.combinations[combination_idx]["type"] == "sequence":
            combo_cards = target_player.combinations[combination_idx]["cards"]
            indices = [VALUES.index(c.value) if not c.is_joker else None for c in combo_cards]
            card_val = VALUES.index(card.value)
            for idx, c in enumerate(combo_cards):
                if c.is_joker:
                    left_val = indices[idx - 1] if idx > 0 else None
                    right_val = indices[idx + 1] if idx < len(indices) - 1 else None
                    if (left_val is not None and card_val == left_val + 1) or (right_val is not None and card_val == right_val - 1):
                        # Reemplazar el joker por la carta real
                        joker_card = combo_cards[idx]
                        combo_cards[idx] = card
                        local_player.remove_from_hand(card)
                        local_player.add_to_hand(joker_card)
                        replaced_joker = True
                        print(f"[DEBUG] Joker reemplazado por {card}, joker {joker_card} devuelto a la mano del jugador.")
                        break
            if not replaced_joker:
                # Agregar la carta normalmente (al inicio o final)
                target_player.combinations[combination_idx]["cards"].append(card)
                local_player.remove_from_hand(card)
        elif target_player.combinations[combination_idx]["type"] == "trio":
            combo_cards = target_player.combinations[combination_idx]["cards"]
            # Si la carta es joker y hay menos de 4 cartas, simplemente agregarlo
            if card.is_joker and len(combo_cards) < 4:
                target_player.combinations[combination_idx]["cards"].append(card)
                local_player.remove_from_hand(card)
                replaced_joker = True
                print(f"[DEBUG] Joker añadido al trío.")
            else:
                # Reemplazar un joker por una carta real
                non_joker_values = [cc.value for cc in combo_cards if not cc.is_joker]
                for idx, c in enumerate(combo_cards):
                    if c.is_joker and non_joker_values and card.value == non_joker_values[0]:
                        joker_card = combo_cards[idx]
                        combo_cards[idx] = card
                        local_player.remove_from_hand(card)
                        local_player.add_to_hand(joker_card)
                        replaced_joker = True
                        print(f"[DEBUG] Joker reemplazado por {card} en trío, joker {joker_card} devuelto a la mano del jugador.")
                        break
                if not replaced_joker:
                    # Agregar la carta normalmente
                    target_player.combinations[combination_idx]["cards"].append(card)
                    local_player.remove_from_hand(card)

        print(f"[DEBUG] Mano del jugador local después: {[str(c) for c in local_player.hand]}")
        print(f"[DEBUG] Combinaciones del jugador objetivo después: {[[str(c) for c in combo['cards']] for combo in target_player.combinations]}")

        # Reordenar si es seguidilla
        if target_player.combinations[combination_idx]["type"] == "sequence":
            target_player.combinations[combination_idx]["cards"].sort(key=lambda c: VALUES.index(c.value))
            print(f"[DEBUG] Combinación reordenada (secuencia): {[str(c) for c in target_player.combinations[combination_idx]['cards']]}")

        # Verificar si ganó la ronda
        if self.check_round_win_condition(local_player):
            print("[DEBUG] El jugador local ha ganado la ronda tras agregar a combinación.")
            self.end_round(winner_idx=self.current_player_idx)

        # Enviar actualización por red
        if self.network.is_host():
            print("[DEBUG] Enviando estado actualizado a los clientes (host).")
            self.network.send_game_state(self.to_dict())
            return True
        else:
            print("[DEBUG] Enviando acción de agregar a combinación al host.")
            self.network.send_action({
                'type': ACTION_ADD_TO_COMBINATION,
                'player_id': self.player_id,
                'card_idx': card_idx,
                'combination_idx': combination_idx,
                'target_player_idx': target_player_idx
            })
            return True

    def can_add_to_combination(self, card, combination_idx, player_idx):
        print(f"[DEBUG] can_add_to_combination: card={card}, combination_idx={combination_idx}, player_idx={player_idx}")
        if player_idx < 0 or player_idx >= len(self.players):
            print(f"[ERROR] player_idx fuera de rango: {player_idx}")
            return False

        target_player = self.players[player_idx]

        if combination_idx < 0 or combination_idx >= len(target_player.combinations):
            print(f"[ERROR] combination_idx fuera de rango: {combination_idx}")
            return False

        combination = target_player.combinations[combination_idx]
        print(f"[DEBUG] Combinación objetivo: {[[str(c) for c in combination['cards']]]}, tipo: {combination['type']}")

        if combination["type"] == "trio":
            # Permitir agregar joker si hay menos de 4 cartas
            if card.is_joker and len(combination["cards"]) < 4:
                print(f"[DEBUG] Joker puede ser añadido al trío.")
                return True
            # Permitir reemplazo de joker por carta real
            non_joker_values = [c.value for c in combination["cards"] if not c.is_joker]
            if non_joker_values and card.value == non_joker_values[0]:
                print(f"[DEBUG] ¿Es trío válido? True")
                return True
            print(f"[DEBUG] ¿Es trío válido? False")
            return False

        elif combination["type"] == "sequence":
            # Permitir reemplazo de joker
            suits = [c.suit for c in combination["cards"] if not c.is_joker]
            if suits and not all(s == card.suit for s in suits):
                print("[DEBUG] Palo no coincide en la secuencia.")
                return False

            indices = [VALUES.index(c.value) if not c.is_joker else None for c in combination["cards"]]
            card_val = VALUES.index(card.value)

            # Si hay un joker en la secuencia, verifica si la carta puede reemplazarlo
            for idx, c in enumerate(combination["cards"]):
                if c.is_joker:
                    left_val = indices[idx - 1] if idx > 0 else None
                    right_val = indices[idx + 1] if idx < len(indices) - 1 else None
                    if (left_val is not None and card_val == left_val + 1) or (right_val is not None and card_val == right_val - 1):
                        print("[DEBUG] Carta puede reemplazar al joker en la secuencia.")
                        return True

            # Si no es reemplazo de joker, ¿puede agregarse al inicio o final?
            non_joker_indices = [i for i in indices if i is not None]
            if not non_joker_indices:
                print("[DEBUG] No hay valores en la secuencia.")
                return False
            min_val = min(non_joker_indices)
            max_val = max(non_joker_indices)
            result = card_val == min_val - 1 or card_val == max_val + 1
            print(f"[DEBUG] ¿Se puede agregar a la secuencia? {result}")
            return result

        print("[DEBUG] Tipo de combinación no soportado.")
        return False
   
    def discard_card(self, card_idx):
        """El jugador actual descarta una carta"""
        if self.state != GAME_STATE_PLAYING:
            return False

        player = self.players[self.current_player_idx]

        # Verificar si el jugador ha tomado una carta
        if not player.took_discard and not player.took_penalty:
            return False

        # Verificar si el índice de la carta es válido
        if card_idx < 0 or card_idx >= len(player.hand):
            return False

        # Descartar la carta
        card = player.hand[card_idx]
        player.remove_from_hand(card)
        self.discard_pile.add(card)

        # Verificar si el jugador ha ganado la ronda después de descartar
        if self.check_round_win_condition(player):
            self.end_round(winner_idx=self.current_player_idx)
        else:
            self.next_player()
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_DISCARD,
                'player_id': self.player_id,
                'card_idx': card_idx
            })
        
        return True
    
    def next_player(self):
        """Pasa al siguiente jugador"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        
        # Reiniciar flags del jugador
        player = self.players[self.current_player_idx]
        player.took_discard = False
        player.took_penalty = False
    
    def check_round_win_condition(self, player):
        """Verifica si un jugador ha cumplido las condiciones para ganar la ronda"""
        # El jugador debe tener 0 cartas en la mano Y haber cumplido el requisito de la ronda
        return len(player.hand) == 0 and player.has_completed_round_requirement
    
    def end_round(self, winner_idx=None):
        """Termina la ronda y calcula las puntuaciones"""
        self.state = GAME_STATE_ROUND_END
        self.round_winner = winner_idx
        self.round_transition_ready = False
        
        # Calcular puntuaciones de la ronda
        self.round_scores = []
        for i, player in enumerate(self.players):
            if i == winner_idx:
                # El ganador no suma puntos
                round_points = 0
            else:
                # Los demás jugadores suman los puntos de las cartas en su mano
                round_points = player.calculate_hand_points()
            
            self.round_scores.append(round_points)
            # Añadir los puntos al total del jugador
            player.score += round_points
        
        print(f"Ronda {self.round_num + 1} terminada. Ganador: Jugador {winner_idx + 1 if winner_idx is not None else 'Ninguno'}")
        print(f"Puntuaciones de la ronda: {self.round_scores}")
        
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
    
    def to_dict(self):
        """Convierte el estado del juego a un diccionario para enviar por la red"""
        try:
            return {
                'players': [player.to_dict() for player in self.players],
                'deck': self.deck.to_dict(),
                'discard_pile': self.discard_pile.to_dict(),
                'current_player_idx': self.current_player_idx,
                'round_num': self.round_num,
                'round_scores': getattr(self, 'round_scores', [0 for _ in self.players]),
                'round_winner': getattr(self, 'round_winner', None),
                'state': self.state,
                'winner': self.winner.id if self.winner else None,
                'eliminated_players': [player.id for player in self.eliminated_players],
                'version': getattr(self, 'version', 0) + 1,  # Incrementa versión
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Error al convertir el juego a diccionario: {e}")
            traceback.print_exc()
            return {}
    
    def update_from_dict(self, data):
        """Actualiza el estado del juego desde un diccionario recibido por la red"""
        try:
            # Actualizar jugadores
            self.players = [Player.from_dict(player_data) for player_data in data['players']]
            
            # Actualizar mazo y descarte
            self.deck = Deck.from_dict(data['deck'])
            self.discard_pile = DiscardPile.from_dict(data['discard_pile'])
            
            # Actualizar estado del juego
            self.current_player_idx = data['current_player_idx']
            self.round_num = data['round_num']
            self.state = data['state']
            self.round_scores = data.get('round_scores', [0 for _ in self.players])
            self.round_winner = data.get('round_winner', None)
    
            # Solo actualiza si el estado es más nuevo
            if hasattr(self, 'version') and data.get('version', 0) <= getattr(self, 'version', 0):
                return
            self.version = data.get('version', 0)
            self.timestamp = data.get('timestamp', 0)
            
            # Actualizar ganador y jugadores eliminados
            if data['winner'] is not None:
                self.winner = next((p for p in self.players if p.id == data['winner']), None)
            else:
                self.winner = None
            
            self.eliminated_players = [p for p in self.players if p.id in data['eliminated_players']]
        except Exception as e:
            print(f"Error al actualizar el juego desde diccionario: {e}")
            traceback.print_exc()
    def handle_network_action(self, action):
        action_type = action.get('type')
        player_id = action.get('player_id')

        if action_type == ACTION_DRAW_DECK:
            if self.current_player_idx == player_id:
                self.take_card_from_deck()
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_DRAW_DISCARD:
            if self.current_player_idx == player_id:
                self.take_card_from_discard(action.get('is_penalty', False))
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_PLAY_COMBINATION:
            if self.current_player_idx == player_id:
                self.lay_down_combination()
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_ADD_TO_COMBINATION:
            self.add_to_combination(
                action['card_idx'],
                action['combination_idx'],
                action.get('target_player_idx'),
                actor_idx=player_id
            )
            if not self.check_and_end_round():
                self.network.send_game_state(self.to_dict())
        elif action_type == ACTION_DISCARD:
            if self.current_player_idx == player_id:
                self.discard_card(action['card_idx'])
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())


    def check_deck_duplicates(self, mensaje=""):
        seen = set()
        for card in self.deck.cards:
            seen.add((card.value, card.suit, id(card)))
            print(f"{mensaje}Total cartas únicas: {len(seen)} / Total en mazo: {len(self.deck.cards)}")
    
    def check_and_end_round(self):
        """Verifica si algún jugador cumplió requisitos y se quedó sin cartas, y termina la ronda si es así."""
        for idx, player in enumerate(self.players):
            if self.check_round_win_condition(player):
                self.end_round(winner_idx=idx)
                return True
        return False