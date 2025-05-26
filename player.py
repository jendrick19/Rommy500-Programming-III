from constants import CARD_VALUES, VALUES, SUITS
from card import Card

class Player:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.hand = []
        self.combinations = []  # Lista de combinaciones bajadas
        self.score = 0  # Puntuación acumulada
        self.is_mano = False  # Indica si el jugador es el "mano" (primer jugador)
        self.has_laid_down = False  # Indica si el jugador ya ha bajado en esta ronda
        self.took_discard = False  # Indica si el jugador tomó la carta de descarte
        self.took_penalty = False  # Indica si el jugador tomó la penalización
    
    def add_to_hand(self, cards):
        if isinstance(cards, list):
            self.hand.extend(cards)
        else:
            self.hand.append(cards)
    
    def remove_from_hand(self, card):
        for i, c in enumerate(self.hand):
            if c == card:
                return self.hand.pop(i)
        return None
    
    def calculate_hand_points(self):
        """Calcula los puntos de las cartas que quedan en la mano"""
        return sum(card.points for card in self.hand)
    
    def can_lay_down(self, round_num):
        """Verifica si el jugador puede bajarse según las reglas de la ronda actual"""
        if round_num == 0:  # Ronda 1: Un Trío y Una Seguidilla
            return self._has_trio() and self._has_sequence()
        elif round_num == 1:  # Ronda 2: Dos Seguidillas
            return self._count_sequences() >= 2
        elif round_num == 2:  # Ronda 3: Tres Tríos
            return self._count_trios() >= 3
        elif round_num == 3:  # Ronda 4: Una Seguidilla y Dos Tríos
            return self._has_sequence() and self._count_trios() >= 2
        return False
    
    def lay_down(self, round_num):
        """Baja las combinaciones requeridas para la ronda actual"""
        if not self.can_lay_down(round_num):
            return False
        
        if round_num == 0:  # Ronda 1: Un Trío y Una Seguidilla
            trio = self._get_trio()
            sequence = self._get_sequence()
            if trio and sequence:
                self.combinations.append({"type": "trio", "cards": trio})
                self.combinations.append({"type": "sequence", "cards": sequence})
                for card in trio + sequence:
                    self.remove_from_hand(card)
                self.has_laid_down = True
                return True
        
        elif round_num == 1:  # Ronda 2: Dos Seguidillas
            sequences = self._get_sequences(2)
            if len(sequences) >= 2:
                for sequence in sequences[:2]:
                    self.combinations.append({"type": "sequence", "cards": sequence})
                    for card in sequence:
                        self.remove_from_hand(card)
                self.has_laid_down = True
                return True
        
        elif round_num == 2:  # Ronda 3: Tres Tríos
            trios = self._get_trios(3)
            if len(trios) >= 3:
                for trio in trios[:3]:
                    self.combinations.append({"type": "trio", "cards": trio})
                    for card in trio:
                        self.remove_from_hand(card)
                self.has_laid_down = True
                return True
        
        elif round_num == 3:  # Ronda 4: Una Seguidilla y Dos Tríos
            sequence = self._get_sequence()
            trios = self._get_trios(2)
            if sequence and len(trios) >= 2:
                self.combinations.append({"type": "sequence", "cards": sequence})
                for card in sequence:
                    self.remove_from_hand(card)
                
                for trio in trios[:2]:
                    self.combinations.append({"type": "trio", "cards": trio})
                    for card in trio:
                        self.remove_from_hand(card)
                
                self.has_laid_down = True
                return True
        
        return False
    
    def can_add_to_combination(self, card, combination_idx, player_idx=None):
        """Verifica si una carta puede ser añadida a una combinación"""
        if player_idx is not None and player_idx != self.id and not self.has_laid_down:
            return False  # No puede añadir a combinaciones de otros si no se ha bajado
        
        target_player = self
        if player_idx is not None and player_idx != self.id:
            # Aquí se debería obtener el jugador con el ID player_idx
            # Como no tenemos acceso directo a otros jugadores, esto se manejará en game.py
            return True  # Asumimos que es válido y se verificará en game.py
        
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
    
    def add_to_combination(self, card, combination_idx):
        """Añade una carta a una combinación existente"""
        if combination_idx >= len(self.combinations):
            return False
        
        combination = self.combinations[combination_idx]
        combination["cards"].append(card)
        
        # Si es una seguidilla, ordenar las cartas
        if combination["type"] == "sequence":
            combination["cards"].sort(key=lambda c: VALUES.index(c.value))
        
        return True
    
    def can_replace_joker(self, card, combination_idx, joker_idx):
        """Verifica si una carta puede reemplazar un Joker en una combinación"""
        if combination_idx >= len(self.combinations):
            return False
        
        combination = self.combinations[combination_idx]
        if joker_idx >= len(combination["cards"]):
            return False
        
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
            if not all(c.suit == temp_cards[0].suit for c in temp_cards):
                return False
            
            # Verificar que los valores forman una secuencia
            values = [VALUES.index(c.value) for c in temp_cards]
            values.sort()
            for i in range(1, len(values)):
                if values[i] != values[i-1] + 1:
                    return False
            
            return True
        
        return False
    
    def replace_joker(self, card, combination_idx, joker_idx):
        """Reemplaza un Joker con una carta de la mano"""
        if not self.can_replace_joker(card, combination_idx, joker_idx):
            return None
        
        combination = self.combinations[combination_idx]
        joker = combination["cards"][joker_idx]
        combination["cards"][joker_idx] = card
        
        # Si es una seguidilla, ordenar las cartas
        if combination["type"] == "sequence":
            combination["cards"].sort(key=lambda c: VALUES.index(c.value))
        
        return joker
    
    def _has_trio(self):
        """Verifica si el jugador tiene un trío en su mano"""
        value_counts = {}
        for card in self.hand:
            if card.is_joker:
                continue
            value_counts[card.value] = value_counts.get(card.value, 0) + 1
        
        # Contar Jokers disponibles
        joker_count = sum(1 for card in self.hand if card.is_joker)
        
        # Verificar si hay un trío (con o sin Jokers)
        for value, count in value_counts.items():
            if count + joker_count >= 3:
                return True
        
        return False
    
    def _has_sequence(self):
        """Verifica si el jugador tiene una seguidilla en su mano"""
        # Agrupar cartas por palo
        suits = {}
        for card in self.hand:
            if card.is_joker:
                continue
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        # Contar Jokers disponibles
        joker_count = sum(1 for card in self.hand if card.is_joker)
        
        # Verificar cada palo
        for suit, cards in suits.items():
            # Ordenar cartas por valor
            cards.sort(key=lambda c: VALUES.index(c.value))
            
            # Buscar secuencias potenciales
            for i in range(len(cards)):
                sequence = [cards[i]]
                available_jokers = joker_count
                
                for j in range(i + 1, len(cards)):
                    next_val_idx = VALUES.index(sequence[-1].value) + 1
                    curr_val_idx = VALUES.index(cards[j].value)
                    
                    # Si es el siguiente valor, añadirlo a la secuencia
                    if curr_val_idx == next_val_idx:
                        sequence.append(cards[j])
                    # Si hay un hueco y tenemos Jokers, usar un Joker
                    elif curr_val_idx > next_val_idx and available_jokers > 0:
                        # Calcular cuántos Jokers necesitamos
                        jokers_needed = curr_val_idx - next_val_idx
                        if jokers_needed <= available_jokers:
                            # Añadir los Jokers necesarios
                            for _ in range(jokers_needed):
                                sequence.append(None)  # Placeholder para Joker
                                available_jokers -= 1
                            sequence.append(cards[j])
                    
                    # Si la secuencia es lo suficientemente larga, hemos terminado
                    if len(sequence) >= 4:
                        return True
                
                # Si la secuencia es casi lo suficientemente larga y tenemos Jokers, completarla
                if len(sequence) + available_jokers >= 4:
                    return True
        
        return False
    
    def _count_sequences(self):
        """Cuenta cuántas seguidillas puede formar el jugador"""
        # Esta es una simplificación; en una implementación real, 
        # necesitaríamos verificar cada combinación posible
        count = 0
        if self._has_sequence():
            count += 1
            # Simular la eliminación de las cartas usadas y verificar de nuevo
            # Esto es una aproximación
            if len(self.hand) >= 8:  # Necesitamos al menos 8 cartas para dos seguidillas
                count += 1
        return count
    
    def _count_trios(self):
        """Cuenta cuántos tríos puede formar el jugador"""
        value_counts = {}
        for card in self.hand:
            if card.is_joker:
                continue
            value_counts[card.value] = value_counts.get(card.value, 0) + 1
        
        # Contar Jokers disponibles
        joker_count = sum(1 for card in self.hand if card.is_joker)
        
        # Contar tríos posibles
        trios = 0
        for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:
                trios += 1
                value_counts[value] -= 3
            elif count + joker_count >= 3:
                jokers_needed = 3 - count
                joker_count -= jokers_needed
                trios += 1
                value_counts[value] = 0
        
        return trios
    
    def _get_trio(self):
        """Obtiene un trío de la mano del jugador"""
        value_counts = {}
        for card in self.hand:
            if not card.is_joker:
                value_counts[card.value] = value_counts.get(card.value, 0) + 1
        
        # Buscar un valor con al menos 3 cartas
        for value, count in value_counts.items():
            if count >= 3:
                # Encontrar las 3 primeras cartas con este valor
                trio = []
                for card in self.hand:
                    if not card.is_joker and card.value == value:
                        trio.append(card)
                        if len(trio) == 3:
                            return trio
                
                # Si no hay suficientes cartas, usar Jokers
                jokers = [card for card in self.hand if card.is_joker]
                if count + len(jokers) >= 3:
                    trio = []
                    # Añadir las cartas con el valor
                    for card in self.hand:
                        if not card.is_joker and card.value == value:
                            trio.append(card)
                    
                    # Añadir los Jokers necesarios
                    jokers_needed = 3 - len(trio)
                    for i in range(jokers_needed):
                        if i < len(jokers):
                            trio.append(jokers[i])
                    
                    return trio
        
        return None
    
    def _get_trios(self, count):
        """Obtiene varios tríos de la mano del jugador"""
        trios = []
        hand_copy = self.hand.copy()
        jokers = [card for card in hand_copy if card.is_joker]
        non_jokers = [card for card in hand_copy if not card.is_joker]
        
        # Contar cartas por valor
        value_counts = {}
        for card in non_jokers:
            value_counts[card.value] = value_counts.get(card.value, 0) + 1
        
        # Ordenar valores por cantidad (primero los que tienen más cartas)
        sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
        
        for value, card_count in sorted_values:
            if len(trios) >= count:
                break
            
            if card_count >= 3:
                # Encontrar 3 cartas con este valor
                trio = []
                for i, card in enumerate(non_jokers):
                    if card.value == value and card in hand_copy:
                        trio.append(card)
                        hand_copy.remove(card)
                        if len(trio) == 3:
                            trios.append(trio)
                            break
            
            elif card_count + len(jokers) >= 3:
                # Usar Jokers para completar el trío
                trio = []
                # Añadir las cartas con el valor
                for i, card in enumerate(non_jokers):
                    if card.value == value and card in hand_copy:
                        trio.append(card)
                        hand_copy.remove(card)
                
                # Añadir los Jokers necesarios
                jokers_needed = 3 - len(trio)
                for i in range(jokers_needed):
                    if jokers and i < len(jokers):
                        trio.append(jokers[0])
                        jokers.remove(jokers[0])
                
                trios.append(trio)
        
        return trios
    
    def _get_sequence(self):
        """Obtiene una seguidilla de la mano del jugador"""
        # Agrupar cartas por palo
        suits = {}
        for card in self.hand:
            if card.is_joker:
                continue
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        # Contar Jokers disponibles
        jokers = [card for card in self.hand if card.is_joker]
        
        # Verificar cada palo
        for suit, cards in suits.items():
            # Ordenar cartas por valor
            cards.sort(key=lambda c: VALUES.index(c.value))
            
            # Buscar la secuencia más larga
            best_sequence = None
            max_length = 0
            
            for i in range(len(cards)):
                sequence = [cards[i]]
                available_jokers = jokers.copy()
                
                for j in range(i + 1, len(cards)):
                    next_val_idx = VALUES.index(sequence[-1].value) + 1
                    curr_val_idx = VALUES.index(cards[j].value)
                    
                    # Si es el siguiente valor, añadirlo a la secuencia
                    if curr_val_idx == next_val_idx:
                        sequence.append(cards[j])
                    # Si hay un hueco y tenemos Jokers, usar un Joker
                    elif curr_val_idx > next_val_idx and available_jokers:
                        # Calcular cuántos Jokers necesitamos
                        jokers_needed = curr_val_idx - next_val_idx
                        if jokers_needed <= len(available_jokers):
                            # Añadir los Jokers necesarios
                            for _ in range(jokers_needed):
                                sequence.append(available_jokers.pop(0))
                            sequence.append(cards[j])
                
                # Si la secuencia es lo suficientemente larga, guardarla
                if len(sequence) >= 4 and len(sequence) > max_length:
                    best_sequence = sequence
                    max_length = len(sequence)
                
                # Si la secuencia es casi lo suficientemente larga y tenemos Jokers, completarla
                elif len(sequence) + len(available_jokers) >= 4 and len(sequence) + len(available_jokers) > max_length:
                    # Añadir los Jokers necesarios al final
                    while len(sequence) < 4:
                        sequence.append(available_jokers.pop(0))
                    
                    best_sequence = sequence
                    max_length = len(sequence)
            
            if best_sequence and len(best_sequence) >= 4:
                return best_sequence
        
        return None
    
    def _get_sequences(self, count):
        """Obtiene varias seguidillas de la mano del jugador"""
        sequences = []
        hand_copy = self.hand.copy()
        
        for _ in range(count):
            # Simular la mano actual
            current_player = Player(self.id, self.name)
            current_player.hand = hand_copy.copy()
            
            # Intentar obtener una seguidilla
            sequence = current_player._get_sequence()
            if sequence and len(sequence) >= 4:
                sequences.append(sequence)
                # Eliminar las cartas usadas
                for card in sequence:
                    if card in hand_copy:
                        hand_copy.remove(card)
            else:
                break
        
        return sequences
    def detect_trios(self):
        """Detecta tríos en la mano (sin quitarlos)"""
        from collections import defaultdict
        value_map = defaultdict(list)
        for card in self.hand:
            if not card.is_joker:
                value_map[card.value].append(card)
    
        trios = []
        for value, cards in value_map.items():
            if len(cards) >= 3:
                trios.append(cards)
        return trios


    def detect_seguidillas(self):
        """Detecta seguidillas (4+ cartas consecutivas del mismo palo)"""
        from collections import defaultdict

        # Orden de valores
        order = {val: i for i, val in enumerate(VALUES)}

        #Agrupar cartas por palo
        suits = defaultdict(list)
        for card in self.hand:
            if not card.is_joker and card.value in order:
                suits[card.suit].append(card)

        seguidillas = []

        for suit, cards in suits.items():
            # Ordenar las cartas por el índice en VALUES
            sorted_cards = sorted(cards, key=lambda c: order[c.value])

            # Buscar secuencias de 4 o más consecutivas
            temp = [sorted_cards[0]]
            for i in range(1, len(sorted_cards)):
                prev_idx = order[sorted_cards[i - 1].value]
                curr_idx = order[sorted_cards[i].value]
                if curr_idx == prev_idx + 1:
                    temp.append(sorted_cards[i])
                elif curr_idx == prev_idx:
                    continue  # Ignorar duplicados
                else:
                    if len(temp) >= 4:
                        seguidillas.append(temp[:])
                    temp = [sorted_cards[i]]
        
        if len(temp) >= 4:
            seguidillas.append(temp)

        return seguidillas


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hand': [card.to_dict() for card in self.hand],
            'combinations': [
                {
                    'type': combo['type'],
                    'cards': [card.to_dict() for card in combo['cards']]
                }
                for combo in self.combinations
            ],
            'score': self.score,
            'is_mano': self.is_mano,
            'has_laid_down': self.has_laid_down,
            'took_discard': self.took_discard,
            'took_penalty': self.took_penalty
        }
    
    @staticmethod
    def from_dict(data):
        player = Player(data['id'], data['name'])
        player.hand = [Card.from_dict(card_data) for card_data in data['hand']]
        player.combinations = [
            {
                'type': combo['type'],
                'cards': [Card.from_dict(card_data) for card_data in combo['cards']]
            }
            for combo in data['combinations']
        ]
        player.score = data['score']
        player.is_mano = data['is_mano']
        player.has_laid_down = data['has_laid_down']
        player.took_discard = data['took_discard']
        player.took_penalty = data['took_penalty']
        return player
