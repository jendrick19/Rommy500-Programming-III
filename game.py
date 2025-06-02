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
        self.rejected_discard = []             # Jugadores que rechazaron la carta del descarte inicial
        self.discard_offer = False     # Inicialmente no hay oferta de descarte
        self.discard_offered_to = -1           # Nadie tiene la oferta inicialmente
        self.discard_origin_player = -1        # No hay jugador origen inicialmente
        
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
                accion = "update"
                print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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
        self.discard_offer = False  # No iniciar oferta automáticamente
        self.rejected_discard = []
        self.discard_offered_to = self.current_player_idx  # El jugador actual es el primero en decidir
        self.discard_origin_player = self.current_player_idx  # El jugador actual es el origen
        
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
            accion = "start_new_round"
            print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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
        
        # Terminar la fase de oferta si estaba activa
        self.discard_offer = False
        self.discard_offered_to = -1
        self.discard_origin_player = -1
        
        # Enviar el estado actualizado
        if self.network.is_host():
            print(f"[HOST] Jugador {self.current_player_idx} tomó del mazo")
            self.network.send_game_state(self.to_dict())
        else:
            self.network.send_action({
                'type': ACTION_DRAW_DECK,
                'player_id': self.player_id
            })
        
        return True
    
    def take_card_from_discard(self, is_penalty=False):
        print(f"[DEBUG] take_card_from_discard llamado con is_penalty={is_penalty}")
        if self.state != GAME_STATE_PLAYING:
            return False

        # Determinar el jugador que toma la carta
        if self.discard_offer:
            player = self.players[self.discard_offered_to]
        else:
            player = self.players[self.current_player_idx]

        # Verificar si el jugador ya tomó una carta
        if player.took_discard or player.took_penalty:
            print("[DEBUG] El jugador ya tomó una carta este turno.")
            return False

        # Tomar la carta superior del descarte
        card = self.discard_pile.take()
        if card:
            player.hand.append(card)
            print(f"[DEBUG] {player} tomó la carta del descarte: {card}")
        else:
            print("[DEBUG] No hay carta en el descarte para tomar.")
            return False

        if self.discard_offer:
            if is_penalty:
                # Penalización: toma carta extra del mazo
                penalty_card = self.deck.deal()
                if penalty_card:
                    player.hand.append(penalty_card)
                    print(f"[DEBUG] {player} tomó carta de penalización del mazo: {penalty_card}")
                player.took_penalty = True
                player.took_discard = False
            else:
                player.took_discard = True
                player.took_penalty = False

            # Terminar la fase de oferta
            self.discard_offer = False
            self.rejected_discard = []
            self.discard_offered_to = -1
            self.discard_origin_player = -1

            # Si tomó con penalización y no era el mano, darle el turno
            if is_penalty and self.current_player_idx != self.players.index(player):
                self.current_player_idx = self.players.index(player)
                for p in self.players:
                    p.is_mano = False
                player.is_mano = True
        else:
            player.took_discard = True
            player.took_penalty = False

        # Enviar el estado actualizado
        if self.network.is_host():
            print(f"[HOST] Jugador {self.current_player_idx} tomó del descarte{' (con penalización)' if is_penalty else ''}")
            self.network.send_game_state(self.to_dict())
        else:
            # Cliente: envía la acción
            self.network.send_action({
                'type': ACTION_DRAW_DISCARD if not is_penalty else 'take_discard_penalty',
                'player_id': self.player_id,
                'is_penalty': is_penalty
            })
            print(f"[CLIENTE] Jugador {self.player_id} tomó del descarte{' (con penalización)' if is_penalty else ''}")
        return True
    
    def reject_discard_offer(self):
        """El jugador actual rechaza la carta del descarte inicial."""
        # Si es cliente, enviar la acción al host
        if not self.network.is_host():
            print(f"[CLIENTE] Jugador {self.player_id} envía acción de rechazo")
            self.network.send_action({
                'type': 'reject_discard',
                'player_id': self.player_id
            })
            return

        print(f"[HOST] Procesando rechazo directo del jugador {self.player_id}")
        # Si es el jugador MANO iniciando la oferta
        if self.current_player_idx == self.player_id and not self.discard_offer:
            print(f"[HOST] Iniciando fase de oferta desde jugador MANO")
            self.discard_offer = True
            self.rejected_discard = [self.player_id]
            self.discard_origin_player = self.player_id
            self.discard_offered_to = (self.player_id + 1) % len(self.players)
            self.players[self.discard_offered_to].took_discard = False
            self.players[self.discard_offered_to].took_penalty = False
            if self.network.is_host():
                print(f"[HOST] Ofreciendo carta al jugador {self.discard_offered_to}")
                self.network.send_game_state(self.to_dict())
            return

        # Si es otro jugador rechazando durante la oferta
        if self.discard_offer and self.discard_offered_to == self.player_id:
            print(f"[HOST] Jugador {self.player_id} rechaza durante la oferta")
            # Asegurarse de agregar SIEMPRE al jugador que rechaza
            if self.player_id not in self.rejected_discard:
                self.rejected_discard.append(self.player_id)
                print(f"[HOST] Rechazaron: {self.rejected_discard}")

            # Buscar siguiente jugador elegible
            current = self.player_id
            next_player = (current + 1) % len(self.players)
            while next_player in self.rejected_discard or next_player == self.discard_origin_player:
                next_player = (next_player + 1) % len(self.players)
                if next_player == current:
                    # Todos los jugadores (excepto el origen) han rechazado
                    next_player = self.discard_origin_player
                    break

            # Si volvimos al jugador origen, termina la oferta
            if next_player == self.discard_origin_player:
                print("[HOST] Todos rechazaron la carta o volvimos al origen. Terminando fase de oferta.")
                self.discard_offer = False
                self.rejected_discard = []
                self.discard_offered_to = self.discard_origin_player
                if self.network.is_host():
                    print(f"[HOST] El jugador {self.current_player_idx} debe tomar del mazo")
                    self.network.send_game_state(self.to_dict())
            else:
                print(f"[HOST] Ahora se ofrece al jugador {next_player}")
                self.discard_offered_to = next_player
                self.players[next_player].took_discard = False
                self.players[next_player].took_penalty = False
                if self.network.is_host():
                    self.network.send_game_state(self.to_dict())

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
                accion = "lay_down_combination"
                print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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
        # Si no se especifica, agregar a una combinación propia
        target_player_idx = player_idx if player_idx is not None else self.current_player_idx
        target_player = self.players[target_player_idx]

        # Solo puedes agregar a combinaciones de otros si ya te bajaste
        if target_player_idx != self.current_player_idx and not current_player.has_laid_down:
            return False

        # Validar índice de carta y combinación
        if card_idx < 0 or card_idx >= len(current_player.hand):
            return False
        
        card = current_player.hand[card_idx]
        
        # Si no se especifica un jugador, usar el jugador actual
        target_player_idx = player_idx if player_idx is not None else self.current_player_idx
        target_player = self.players[target_player_idx]
        
        # Verificar si el índice de la combinación es válido
        if combination_idx < 0 or combination_idx >= len(target_player.combinations):
            return False

        card = current_player.hand[card_idx]
        combination = target_player.combinations[combination_idx]

        # Validar si la carta puede agregarse a la combinación
        if combination["type"] == "trio":
            if not all(card.value == c.value for c in combination["cards"]):
                return False
        elif combination["type"] == "sequence":
            if not all(card.suit == c.suit for c in combination["cards"]):
                return False
            values = [VALUES.index(c.value) for c in combination["cards"]]
            card_val = VALUES.index(card.value)
            if not (card_val == min(values) - 1 or card_val == max(values) + 1):
                return False
        else:
            return False

        # Agregar la carta
        target_player.combinations[combination_idx]["cards"].append(card)
        current_player.remove_from_hand(card)
        
        # Si es una seguidilla, ordenar las cartas
        if target_player.combinations[combination_idx]["type"] == "sequence":
            target_player.combinations[combination_idx]["cards"].sort(key=lambda c: VALUES.index(c.value))
        
        # Verificar si el jugador ha ganado la ronda
        if self.check_round_win_condition(current_player):
            self.end_round(winner_idx=self.current_player_idx)
        
        # Enviar el estado actualizado
        if self.network.is_host():
            accion = "add_to_combination"
            print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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
        
        # Verificar si el jugador ha ganado la ronda
        if self.check_round_win_condition(current_player):
            self.end_round(winner_idx=self.current_player_idx)
        
        # Enviar el estado actualizado
        if self.network.is_host():
            accion = "replace_joker"
            print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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

        # Verificar si el jugador ha ganado la ronda después de descartar
        if self.check_round_win_condition(player):
            self.end_round(winner_idx=self.current_player_idx)
        else:
            # Pasar al siguiente jugador e iniciar la fase de oferta
            old_player_idx = self.current_player_idx
            self.next_player()
            
            # Iniciar la fase de oferta para el siguiente jugador
            self.discard_offer = False  # No iniciar oferta automáticamente
            self.rejected_discard = []
            self.discard_offered_to = self.current_player_idx  # El jugador actual es el primero en decidir
            self.discard_origin_player = self.current_player_idx  # El jugador actual es el origen

            if self.network.is_host():
                print(f"[HOST] Jugador {old_player_idx} descartó. Turno del jugador {self.current_player_idx}")
                self.network.send_game_state(self.to_dict())

        # Enviar el estado actualizado
        if not self.network.is_host():
            self.network.send_action({
                'type': ACTION_DISCARD,
                'player_id': self.player_id,
                'card_idx': card_idx
            })
        
        return True
    
    def next_player(self):
        """Pasa al siguiente jugador"""
        # Quitar el flag de mano al jugador actual
        self.players[self.current_player_idx].is_mano = False
    
        # Avanzar al siguiente jugador
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
    
        # Asignar el flag de mano al nuevo jugador
        self.players[self.current_player_idx].is_mano = True
    
        # Reiniciar flags del jugador
        player = self.players[self.current_player_idx]
        player.took_discard = False
        player.took_penalty = False
        
        # Iniciar fase de oferta de descarte
        self.discard_offer = False  # No iniciar oferta automáticamente
        self.rejected_discard = []
        self.discard_offered_to = self.current_player_idx  # El jugador actual es el primero en decidir
        self.discard_origin_player = self.current_player_idx  # El jugador actual es el origen
    
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
            accion = "end_round"
            print(f"[HOST] Acción: {accion}, Estado antes de enviar: ronda={self.round_num}, jugador={self.current_player_idx}, estado={self.state}")
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
                'discard_offer': self.discard_offer,  
                'discard_offered_to': self.discard_offered_to,  
                'discard_origin_player': self.discard_origin_player,  
                'rejected_discard': self.rejected_discard,  
                'version': getattr(self, 'version', 0) + 1,  # Incrementa versión
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Error al convertir el juego a diccionario: {e}")
            traceback.print_exc()
            return {}
    
    def update_from_dict(self, data):
        print(f"[UI] ¿Mostrar botones? discard_offer={self.discard_offer}, "
          f"discard_offered_to={self.discard_offered_to}, "
          f"player_id={self.player_id}, ")
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
            self.discard_offer = data.get('discard_offer', False)
            self.discard_offered_to = data.get('discard_offered_to', -1)
            self.discard_origin_player = data.get('discard_origin_player', -1)
            self.rejected_discard = data.get('rejected_discard', [])
            
    
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

        print(f"[HOST] Recibida acción {action_type} del jugador {player_id}")

        if action_type == ACTION_DRAW_DECK:
            if self.current_player_idx == player_id:
                self.take_card_from_deck()
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == 'reject_discard':
            print(f"[HOST] Procesando rechazo del jugador {player_id}")
            # Si es el jugador MANO iniciando la oferta
            if self.current_player_idx == player_id and not self.discard_offer:
                print(f"[HOST] Iniciando fase de oferta desde jugador MANO")
                self.discard_offer = True
                self.rejected_discard = [player_id]
                self.discard_origin_player = player_id
                self.discard_offered_to = (player_id + 1) % len(self.players)
                self.players[self.discard_offered_to].took_discard = False
                self.players[self.discard_offered_to].took_penalty = False
                print(f"[HOST] Iniciando oferta: discard_offer={self.discard_offer}, "
                    f"rejected_discard={self.rejected_discard}, "
                    f"discard_origin_player={self.discard_origin_player}, "
                    f"discard_offered_to={self.discard_offered_to}")
            # Si es otro jugador durante la oferta
            elif self.discard_offer and self.discard_offered_to == player_id:
                print(f"[HOST] Jugador {player_id} rechaza durante la oferta")
                # Asegurarse de agregar SIEMPRE al jugador que rechaza
                if player_id not in self.rejected_discard:
                    self.rejected_discard.append(player_id)
                    print(f"[HOST] Rechazaron: {self.rejected_discard}")

                # Buscar siguiente jugador elegible
                current = player_id
                next_player = (current + 1) % len(self.players)
                while next_player in self.rejected_discard or next_player == self.discard_origin_player:
                    next_player = (next_player + 1) % len(self.players)
                    if next_player == current:
                        # Todos los jugadores (excepto el origen) han rechazado
                        next_player = self.discard_origin_player
                        break

                # Si volvimos al jugador origen, termina la oferta
                if next_player == self.discard_origin_player:
                    print("[HOST] Todos rechazaron la carta o volvimos al origen. Terminando fase de oferta.")
                    self.discard_offer = False
                    self.rejected_discard = []
                    self.discard_offered_to = self.discard_origin_player
                    if self.network.is_host():
                        print(f"[HOST] El jugador {self.current_player_idx} debe tomar del mazo")
                        self.network.send_game_state(self.to_dict())
                else:
                    print(f"[HOST] Ahora se ofrece al jugador {next_player}")
                    self.discard_offered_to = next_player
                    self.players[next_player].took_discard = False
                    self.players[next_player].took_penalty = False
                    if self.network.is_host():
                        self.network.send_game_state(self.to_dict())

                print(f"[HOST] Estado después del rechazo: oferta={self.discard_offer}, ofrecido_a={self.discard_offered_to}")
                self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_DRAW_DISCARD:
            if self.current_player_idx == player_id:
                self.take_card_from_discard(action.get('is_penalty', False))
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == 'take_discard_penalty':
            # Permitir que el jugador tome del descarte con penalización durante la oferta
            if self.discard_offer and self.discard_offered_to == player_id:
                print(f"[HOST] Jugador {player_id} toma del descarte con penalización")
                self.take_card_from_discard(is_penalty=True)
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())
        elif action_type == ACTION_PLAY_COMBINATION:
            if self.current_player_idx == player_id:
                self.lay_down_combination()
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_ADD_TO_COMBINATION:
            if self.current_player_idx == player_id:
                self.add_to_combination(
                    action['card_idx'],
                    action['combination_idx'],
                    action.get('target_player_idx')
                )
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_DISCARD:
            if self.current_player_idx == player_id:
                self.discard_card(action['card_idx'])
                if not self.check_and_end_round():
                    self.network.send_game_state(self.to_dict())

        elif action_type == ACTION_REPLACE_JOKER:
            if self.current_player_idx == player_id:
                self.replace_joker(
                    action['card_idx'],
                    action['combination_idx'],
                    action['joker_idx'],
                    action.get('target_player_idx')
                )
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