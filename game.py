import json
import random
import pygame
import traceback
from constants import *
from card import Card, Deck, DiscardPile
from player import Player

class Game:
    def __init__(self, network):
        self.network = network
        self.players = []
        self.deck = Deck()
        self.discard_pile = DiscardPile()
        self.current_player_idx = 0
        self.round_num = 0
        self.state = GAME_STATE_WAITING
        self.winner = None
        self.eliminated_players = []
        self.player_id = network.get_id()  # ID del jugador local
        
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
            self.deck.reset()
            for player in self.players:
                player.add_to_hand(self.deck.deal(10))
            
            # Colocar la primera carta en el descarte
            self.discard_pile.add(self.deck.deal())
            
            # Establecer el estado del juego
            self.state = GAME_STATE_PLAYING
            
            # Enviar el estado inicial a todos los jugadores
            self.network.send_game_state(self.to_dict())
            print("Estado inicial del juego enviado a todos los jugadores")
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
            # Aquí se manejarían los clics del ratón para las acciones del juego
            # Como tomar cartas, jugar combinaciones, etc.
            pass
    
    def update(self):
        """Actualiza el estado del juego"""
        # Recibir actualizaciones de la red
        game_state = self.network.receive_game_state()
        if game_state:
            try:
                self.update_from_dict(game_state)
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
                self.start_new_round()
            return
    
    def start_new_round(self):
        """Inicia una nueva ronda (solo el host)"""
        # Incrementar el número de ronda
        self.round_num = (self.round_num + 1) % len(ROUNDS)
        
        # Reiniciar el mazo y el descarte
        self.deck.reset()
        self.discard_pile = DiscardPile()
        
        # Reiniciar los jugadores
        for player in self.players:
            player.hand = []
            player.combinations = []
            player.has_laid_down = False
            player.took_discard = False
            player.took_penalty = False
        
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
        
        # Verificar si el jugador ya se ha bajado
        if player.has_laid_down:
            return False
        
        # Verificar si el jugador puede bajarse
        if not player.can_lay_down(self.round_num):
            return False
        
        # Bajar las combinaciones
        if not player.lay_down(self.round_num):
            return False
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_PLAY_COMBINATION,
                'player_id': self.player_id
            })
        
        return True
    
    def add_to_combination(self, card_idx, combination_idx, player_idx=None):
        """Añade una carta a una combinación existente"""
        if self.state != GAME_STATE_PLAYING:
            return False
        
        current_player = self.players[self.current_player_idx]
        
        # Verificar si el jugador se ha bajado
        if not current_player.has_laid_down:
            return False
        
        # Verificar si el índice de la carta es válido
        if card_idx < 0 or card_idx >= len(current_player.hand):
            return False
        
        card = current_player.hand[card_idx]
        
        # Si no se especifica un jugador, usar el jugador actual
        target_player_idx = player_idx if player_idx is not None else self.current_player_idx
        target_player = self.players[target_player_idx]
        
        # Verificar si el índice de la combinación es válido
        if combination_idx < 0 or combination_idx >= len(target_player.combinations):
            return False
        
        # Verificar si la carta puede ser añadida a la combinación
        if not self.can_add_to_combination(card, combination_idx, target_player_idx):
            return False
        
        # Añadir la carta a la combinación
        target_player.combinations[combination_idx]["cards"].append(card)
        current_player.remove_from_hand(card)
        
        # Si es una seguidilla, ordenar las cartas
        if target_player.combinations[combination_idx]["type"] == "sequence":
            target_player.combinations[combination_idx]["cards"].sort(key=lambda c: VALUES.index(c.value))
        
        # Verificar si el jugador ha ganado la ronda
        if len(current_player.hand) == 0:
            self.end_round()
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_ADD_TO_COMBINATION,
                'player_id': self.player_id,
                'card_idx': card_idx,
                'combination_idx': combination_idx,
                'target_player_idx': target_player_idx
            })
        
        return True
    
    def can_add_to_combination(self, card, combination_idx, player_idx):
        """Verifica si una carta puede ser añadida a una combinación"""
        target_player = self.players[player_idx]
        
        if combination_idx >= len(target_player.combinations):
            return False
        
        combination = target_player.combinations[combination_idx]
        
        if combination["type"] == "trio":
            # Para un trío, la carta debe tener el mismo valor
            return any(card.value == c.value for c in combination["cards"])
        
        elif combination["type"] == "sequence":
            # Para una seguidilla, la carta debe ser del mismo palo y continuar la secuencia
            if not all(card.suit == c.suit for c in combination["cards"]):
                return False
            
            # Ordenar las cartas por valor
            sequence_values = [VALUES.index(c.value) for c in combination["cards"]]
            min_val = min(sequence_values)
            max_val = max(sequence_values)
            
            # Verificar si la carta puede añadirse al principio o al final
            card_val = VALUES.index(card.value)
            return card_val == min_val - 1 or card_val == max_val + 1
        
        return False
    
    def replace_joker(self, card_idx, combination_idx, joker_idx, player_idx=None):
        """Reemplaza un Joker con una carta de la mano"""
        if self.state != GAME_STATE_PLAYING:
            return False
        
        current_player = self.players[self.current_player_idx]
        
        # Verificar si el jugador se ha bajado
        if not current_player.has_laid_down:
            return False
        
        # Verificar si el índice de la carta es válido
        if card_idx < 0 or card_idx >= len(current_player.hand):
            return False
        
        card = current_player.hand[card_idx]
        
        # Si no se especifica un jugador, usar el jugador actual
        target_player_idx = player_idx if player_idx is not None else self.current_player_idx
        target_player = self.players[target_player_idx]
        
        # Verificar si los índices son válidos
        if combination_idx < 0 or combination_idx >= len(target_player.combinations):
            return False
        
        combination = target_player.combinations[combination_idx]
        
        if joker_idx < 0 or joker_idx >= len(combination["cards"]):
            return False
        
        joker_card = combination["cards"][joker_idx]
        
        # Verificar si la carta a reemplazar es un Joker
        if not joker_card.is_joker:
            return False
        
        # Verificar si la carta puede reemplazar al Joker
        if not self.can_replace_joker(card, combination, joker_idx):
            return False
        
        # Reemplazar el Joker
        combination["cards"][joker_idx] = card
        current_player.remove_from_hand(card)
        current_player.add_to_hand(joker_card)
        
        # Si es una seguidilla, ordenar las cartas
        if combination["type"] == "sequence":
            combination["cards"].sort(key=lambda c: VALUES.index(c.value))
        
        # Enviar el estado actualizado
        if self.network.is_host():
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_REPLACE_JOKER,
                'player_id': self.player_id,
                'card_idx': card_idx,
                'combination_idx': combination_idx,
                'joker_idx': joker_idx,
                'target_player_idx': target_player_idx
            })
        
        return True
    
    def can_replace_joker(self, card, combination, joker_idx):
        """Verifica si una carta puede reemplazar un Joker en una combinación"""
        joker_card = combination["cards"][joker_idx]
        if not joker_card.is_joker:
            return False
        
        # Para un trío, la carta debe tener el mismo valor que las demás
        if combination["type"] == "trio":
            non_joker_cards = [c for c in combination["cards"] if not c.is_joker]
            if not non_joker_cards:
                return True  # Si solo hay Jokers, cualquier carta puede reemplazarlo
            return card.value == non_joker_cards[0].value
        
        # Para una seguidilla, la carta debe encajar en la posición del Joker
        elif combination["type"] == "sequence":
            # Crear una copia de la combinación con la carta reemplazando al Joker
            temp_cards = combination["cards"].copy()
            temp_cards[joker_idx] = card
            
            # Verificar que todas las cartas son del mismo palo
            if not all(c.suit == temp_cards[0].suit for c in temp_cards if not c.is_joker):
                return False
            
            # Verificar que los valores forman una secuencia
            non_joker_cards = [(i, c) for i, c in enumerate(temp_cards) if not c.is_joker]
            if not non_joker_cards:
                return True  # Si solo hay Jokers, cualquier carta puede reemplazarlo
            
            # Ordenar por valor
            non_joker_cards.sort(key=lambda x: VALUES.index(x[1].value))
            
            # Verificar que la secuencia es válida
            for i in range(1, len(non_joker_cards)):
                prev_idx, prev_card = non_joker_cards[i-1]
                curr_idx, curr_card = non_joker_cards[i]
                
                # Calcular la diferencia de valores
                prev_val = VALUES.index(prev_card.value)
                curr_val = VALUES.index(curr_card.value)
                diff = curr_val - prev_val
                
                # Verificar que la diferencia es correcta considerando los Jokers entre medias
                jokers_between = sum(1 for idx in range(prev_idx + 1, curr_idx) if temp_cards[idx].is_joker)
                if diff != jokers_between + 1:
                    return False
            
            return True
        
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
        
        # Verificar si el jugador ha ganado la ronda
        if len(player.hand) == 0:
            self.end_round()
        else:
            # Pasar al siguiente jugador
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
    
    def end_round(self):
        """Finaliza la ronda actual"""
        # Calcular puntos para los jugadores que no se bajaron
        for player in self.players:
            if not player.has_laid_down:
                points = player.calculate_hand_points()
                player.score += points
        
        # Verificar si algún jugador ha sido eliminado
        for i, player in enumerate(self.players):
            if player.score >= 500 and player not in self.eliminated_players:
                self.eliminated_players.append(player)
        
        # Verificar si solo queda un jugador
        active_players = [p for p in self.players if p not in self.eliminated_players]
        if len(active_players) == 1:
            self.winner = active_players[0]
            self.state = GAME_STATE_GAME_END
        else:
            self.state = GAME_STATE_ROUND_END
    
    def to_dict(self):
        """Convierte el estado del juego a un diccionario para enviar por la red"""
        try:
            return {
                'players': [player.to_dict() for player in self.players],
                'deck': self.deck.to_dict(),
                'discard_pile': self.discard_pile.to_dict(),
                'current_player_idx': self.current_player_idx,
                'round_num': self.round_num,
                'state': self.state,
                'winner': self.winner.id if self.winner else None,
                'eliminated_players': [player.id for player in self.eliminated_players]
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
        """Procesa una acción recibida de un cliente (solo el host)"""
        action_type = action.get('type')
        player_id = action.get('player_id')
        if action_type == ACTION_DRAW_DECK:
            if self.current_player_idx == player_id:
                self.take_card_from_deck()
        elif action_type == ACTION_DRAW_DISCARD:
            if self.current_player_idx == player_id:
                self.take_card_from_discard(action.get('is_penalty', False))
        elif action_type == ACTION_PLAY_COMBINATION:
            if self.current_player_idx == player_id:
                self.lay_down_combination()
        elif action_type == ACTION_ADD_TO_COMBINATION:
            if self.current_player_idx == player_id:
                self.add_to_combination(
                    action['card_idx'],
                    action['combination_idx'],
                    action.get('target_player_idx')
                )
        elif action_type == ACTION_DISCARD:
            if self.current_player_idx == player_id:
                self.discard_card(action['card_idx'])
        elif action_type == ACTION_REPLACE_JOKER:
            if self.current_player_idx == player_id:
                self.replace_joker(
                    action['card_idx'],
                    action['combination_idx'],
                    action['joker_idx'],
                    action.get('target_player_idx')
                )