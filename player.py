from constants import CARD_VALUES, VALUES, SUITS
from card import Card

class Player:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.hand = []
        self.combinations = []
        self.score = 0
        self.is_mano = False
        self.has_laid_down = False
        self.took_discard = False
        self.took_penalty = False
        self.has_laid_down_trio = False
        self.has_laid_down_sequence = False
        self.sequences_laid_down = 0
        self.trios_laid_down = 0
        self.has_completed_round_requirement = False  # Nuevo flag

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
        # Siempre puede bajarse si tiene un trío o seguidilla
        return self._has_trio() or self._has_sequence()

    def lay_down(self, round_num):
        """Baja todas las combinaciones posibles en la mano"""
        laid_down = False
        initial_trios = self.trios_laid_down
        initial_sequences = self.sequences_laid_down
        
        # Bajar todos los tríos posibles
        while self._has_trio():
            trio = self._get_trio()
            if trio:
                self.combinations.append({"type": "trio", "cards": trio})
                for card in trio:
                    self.remove_from_hand(card)
                self.trios_laid_down += 1
                laid_down = True
        
        # Bajar todas las seguidillas posibles
        while self._has_sequence():
            sequence = self._get_sequence()
            if sequence:
                self.combinations.append({"type": "sequence", "cards": sequence})
                for card in sequence:
                    self.remove_from_hand(card)
                self.sequences_laid_down += 1
                laid_down = True

        # Verificar si cumplió el requisito mínimo de la ronda
        if not self.has_completed_round_requirement:
            total_trios = self.trios_laid_down
            total_sequences = self.sequences_laid_down
            
            if round_num == 0:  # Ronda 1: Un Trío y Una Seguidilla
                if total_trios >= 1 and total_sequences >= 1:
                    self.has_completed_round_requirement = True
                    print(f"Jugador {self.id + 1} cumplió requisito ronda 1: {total_trios} tríos, {total_sequences} seguidillas")
            elif round_num == 1:  # Ronda 2: Dos Seguidillas
                if total_sequences >= 2:
                    self.has_completed_round_requirement = True
                    print(f"Jugador {self.id + 1} cumplió requisito ronda 2: {total_sequences} seguidillas")
            elif round_num == 2:  # Ronda 3: Tres Tríos
                if total_trios >= 3:
                    self.has_completed_round_requirement = True
                    print(f"Jugador {self.id + 1} cumplió requisito ronda 3: {total_trios} tríos")
            elif round_num == 3:  # Ronda 4: Una Seguidilla y Dos Tríos (Ronda Completa)
                if total_trios >= 2 and total_sequences >= 1:
                    self.has_completed_round_requirement = True
                    print(f"Jugador {self.id + 1} cumplió requisito ronda 4: {total_trios} tríos, {total_sequences} seguidillas")

        if laid_down:
            self.has_laid_down = True
            print(f"Jugador {self.id + 1} se bajó. Cartas restantes: {len(self.hand)}, Requisito cumplido: {self.has_completed_round_requirement}")
        
        return laid_down

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
        # Agrupar cartas por palo
        suits = {}
        for card in self.hand:
            if card.is_joker:
                continue
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        joker_count = sum(1 for card in self.hand if card.is_joker)
        
        for suit, cards in suits.items():
            cards.sort(key=lambda c: VALUES.index(c.value))
            for i in range(len(cards)):
                sequence = [cards[i]]
                available_jokers = joker_count
                last_val = VALUES.index(cards[i].value)
                for j in range(i + 1, len(cards)):
                    next_val = VALUES.index(cards[j].value)
                    gap = next_val - last_val - 1
                    if gap == 0:
                        sequence.append(cards[j])
                        last_val = next_val
                    elif gap > 0 and available_jokers >= gap:
                        sequence.extend([None]*gap)  # Jokers como comodines
                        sequence.append(cards[j])
                        available_jokers -= gap
                        last_val = next_val
                    else:
                        break
                if len(sequence) + available_jokers >= 4:
                    return True
        # Si hay suficientes Jokers, pueden formar una secuencia solos
        if joker_count >= 4:
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
        jokers = [card for card in self.hand if card.is_joker]
        non_jokers = [card for card in self.hand if not card.is_joker]
        
        # Caso especial: solo jokers
        if len(jokers) >= 3:
            return jokers[:3]
        
        # Agrupar cartas por valor
        value_counts = {}
        for card in non_jokers:
            value_counts[card.value] = value_counts.get(card.value, 0) + 1
        
        # Buscar un valor con al menos 2 cartas (para completar con 1 joker)
        for value, count in value_counts.items():
            if count >= 2 and jokers:
                trio = [card for card in non_jokers if card.value == value][:2]
                trio.append(jokers[0])
                return trio
            elif count >= 3:
                return [card for card in non_jokers if card.value == value][:3]
        
        # Si hay suficientes jokers para un trío
        if len(jokers) >= 3:
            return jokers[:3]
        
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
        """Obtiene una seguidilla de la mano del jugador, usando Jokers como comodines."""
        jokers = [card for card in self.hand if card.is_joker]
        non_jokers = [card for card in self.hand if not card.is_joker]
        
        # Caso especial: solo jokers
        if len(jokers) >= 4:
            return jokers[:4]
        
        # Agrupar cartas por palo
        suits = {}
        for card in non_jokers:
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)
        
        for suit, cards in suits.items():
            if not cards:
                continue
            
            # Ordenar cartas por valor
            cards.sort(key=lambda c: VALUES.index(c.value))
            
            # Intentar construir secuencias
            for i in range(len(cards)):
                sequence = [cards[i]]
                available_jokers = jokers.copy()
                
                current_val = VALUES.index(cards[i].value)
                
                # Intentar extender la secuencia hacia adelante
                for next_val in range(current_val + 1, len(VALUES)):
                    # Buscar carta con el siguiente valor
                    found = False
                    for card in cards:
                        if VALUES.index(card.value) == next_val and card not in sequence:
                            sequence.append(card)
                            found = True
                            break
                    
                    if not found:
                        if available_jokers:
                            sequence.append(available_jokers.pop(0))
                        else:
                            break
                
                if len(sequence) >= 4:
                    return sequence
                
                # Intentar extender hacia atrás con jokers
                if available_jokers:
                    first_val = VALUES.index(sequence[0].value)
                    needed = first_val - 0  # Cuántos necesitamos para llegar al inicio
                    if len(available_jokers) >= needed:
                        for _ in range(needed):
                            sequence.insert(0, available_jokers.pop(0))
                        if len(sequence) >= 4:
                            return sequence
        
        # Si no se encontró ninguna secuencia, verificar si hay suficientes jokers
        if len(jokers) >= 4:
            return jokers[:4]
        
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
        """Detecta tríos (3 cartas del mismo valor) incluyendo Jokers"""
        from collections import defaultdict

        value_map = defaultdict(list)
        jokers = [card for card in self.hand if card.is_joker]

        for card in self.hand:
            if not card.is_joker:
                value_map[card.value].append(card)

        trios = []

        for value, cards in value_map.items():
            needed = 3 - len(cards)
            if needed <= len(jokers):
                # Crear trío con cartas + jokers necesarios
                trio = cards + jokers[:needed]
                trios.append(trio)

        return trios

    def detect_seguidillas(self):
        """Detecta seguidillas (4+ cartas consecutivas del mismo palo) incluyendo Jokers"""
        from collections import defaultdict

        order = {val: i for i, val in enumerate(VALUES)}
        suits = defaultdict(list)

        # Separar jokers
        jokers = [card for card in self.hand if card.is_joker]

        # Agrupar no-jokers por palo
        for card in self.hand:
            if not card.is_joker and card.value in order:
                suits[card.suit].append(card)

        seguidillas = []

        for suit, cards in suits.items():
            if not cards:
                continue

            # Ordenar por valor
            sorted_cards = sorted(cards, key=lambda c: order[c.value])

            for i in range(len(sorted_cards)):
                sequence = [sorted_cards[i]]
                used_jokers = []

                for j in range(i + 1, len(sorted_cards)):
                    prev_val = order[sequence[-1].value]
                    curr_val = order[sorted_cards[j].value]

                    gap = curr_val - prev_val

                    if gap == 0:
                        continue  # duplicado, saltar
                    elif gap == 1:
                        sequence.append(sorted_cards[j])
                    elif gap > 1:
                        # Necesitamos gap-1 jokers
                        needed = gap - 1
                        if len(jokers) - len(used_jokers) >= needed:
                            # Añadir jokers intermedios
                            for _ in range(needed):
                                sequence.append(jokers[len(used_jokers)])
                                used_jokers.append(jokers[len(used_jokers)])
                            sequence.append(sorted_cards[j])
                        else:
                            break  # no se puede continuar

                    # Si la secuencia es válida (4+), guárdala
                    if len(sequence) >= 4 and sequence not in seguidillas:
                        seguidillas.append(sequence.copy())

                # También verificar secuencias cortas al final
                if len(sequence) >= 4 and sequence not in seguidillas:
                    seguidillas.append(sequence.copy())

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
            'took_penalty': self.took_penalty,
            'has_laid_down_trio': self.has_laid_down_trio,
            'has_laid_down_sequence': self.has_laid_down_sequence,
            'sequences_laid_down': self.sequences_laid_down,
            'trios_laid_down': self.trios_laid_down,
            'has_completed_round_requirement': self.has_completed_round_requirement
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
        player.has_laid_down_trio = data.get('has_laid_down_trio', False)
        player.has_laid_down_sequence = data.get('has_laid_down_sequence', False)
        player.sequences_laid_down = data.get('sequences_laid_down', 0)
        player.trios_laid_down = data.get('trios_laid_down', 0)
        player.has_completed_round_requirement = data.get('has_completed_round_requirement', False)
        return player
