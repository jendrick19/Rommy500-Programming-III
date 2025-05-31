from constants import CARD_VALUES, VALUES, SUITS
from card import Card
ALT_VALUES = VALUES[1:] + ['A']

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
        if player_idx is not None and player_idx != self.id and not self.has_laid_down:
            return False

        target_player = self
        if player_idx is not None and player_idx != self.id:
            return True  # Se valida en game.py

        if combination_idx >= len(target_player.combinations):
            return False

        combination = target_player.combinations[combination_idx]

        if combination["type"] == "trio":
            return any(card.value == c.value for c in combination["cards"])

        elif combination["type"] == "sequence":
            # Validar que todas las cartas + nueva son del mismo palo
            if not all(c.suit == card.suit for c in combination["cards"]):
                return False

            # Obtener la lista de valores de la secuencia actual
            current_values = [c.value for c in combination["cards"]]
            value_list = VALUES  # Orden base circular

            # Buscar índices circulares
            indices = sorted([value_list.index(v) for v in current_values])
            card_idx = value_list.index(card.value)

            # Verificar si se puede añadir antes o después en orden circular
            first_idx = indices[0]
            last_idx = indices[-1]

            diff_before = (first_idx - card_idx) % len(value_list)
            diff_after = (card_idx - last_idx) % len(value_list)

            return diff_before == 1 or diff_after == 1

        return False

    
    def add_to_combination(self, card, combination_idx):
        if combination_idx >= len(self.combinations):
            return False

        combination = self.combinations[combination_idx]
        combination["cards"].append(card)

        if combination["type"] == "sequence":
            combination["cards"] = self._order_circular_sequence(combination["cards"])

        return True

    
    def can_replace_joker(self, card, combination_idx, joker_idx):
        if combination_idx >= len(self.combinations):
            return False

        combination = self.combinations[combination_idx]
        if joker_idx >= len(combination["cards"]):
            return False

        joker_card = combination["cards"][joker_idx]
        if not joker_card.is_joker:
            return False

        if combination["type"] == "trio":
            non_jokers = [c for c in combination["cards"] if not c.is_joker]
            return card.value == non_jokers[0].value if non_jokers else True

        elif combination["type"] == "sequence":
            value_list = VALUES
            cards_copy = combination["cards"][:]
            cards_copy[joker_idx] = card

            if not all(c.suit == cards_copy[0].suit for c in cards_copy if not c.is_joker):
                return False

            # Convertir a índices circulares
            indices = sorted([value_list.index(c.value) for c in cards_copy if not c.is_joker])
            for i in range(1, len(indices)):
                prev = indices[i - 1]
                curr = indices[i]
                gap = (curr - prev) % len(value_list)
                if gap != 1:
                    return False

            return True

        return False

    
    def replace_joker(self, card, combination_idx, joker_idx):
        if not self.can_replace_joker(card, combination_idx, joker_idx):
            return None

        combination = self.combinations[combination_idx]
        joker = combination["cards"][joker_idx]
        combination["cards"][joker_idx] = card

        # Si es una seguidilla, ordenar circularmente
        if combination["type"] == "sequence":
            combination["cards"] = self._order_circular_sequence(combination["cards"])

        return joker

    
    def _order_circular_sequence(self, cards):
        """Ordena una secuencia circularmente coherente"""
        value_list = VALUES

        # Excluir Jokers para encontrar el orden base
        non_jokers = [c for c in cards if not c.is_joker]
        if not non_jokers:
            return cards

        # Buscar el punto de inicio que mejor preserve la secuencia circular
        indices = [value_list.index(c.value) for c in non_jokers]
        best_order = cards
        min_disorder = float('inf')

        for start in indices:
            rotated = sorted(indices, key=lambda i: (i - start) % len(value_list))
            expected = [(rotated[0] + i) % len(value_list) for i in range(len(rotated))]
            disorder = sum(abs(a - b) for a, b in zip(rotated, expected))
            if disorder < min_disorder:
                min_disorder = disorder
                best_order = sorted(cards, key=lambda c: (value_list.index(c.value) - start) % len(value_list) if not c.is_joker else 999)

        return best_order

    
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
        for use_alt_values in [False, True]:
            value_list = ALT_VALUES if use_alt_values else VALUES
            if self._has_sequence_with_values(value_list):
                return True
        return False

    def _has_sequence_with_values(self, value_list):
        suits = {}
        for card in self.hand:
            if card.is_joker:
                continue
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)

        joker_count = sum(1 for card in self.hand if card.is_joker)

        for suit, cards in suits.items():
            sorted_cards = sorted(cards, key=lambda c: value_list.index(c.value))
            for i in range(len(sorted_cards)):
                sequence = [sorted_cards[i]]
                available_jokers = joker_count
                for j in range(i + 1, len(sorted_cards)):
                    prev_idx = value_list.index(sequence[-1].value)
                    curr_idx = value_list.index(sorted_cards[j].value)

                    gap = curr_idx - prev_idx
                    if gap == 1:
                        sequence.append(sorted_cards[j])
                    elif gap > 1 and available_jokers >= (gap - 1):
                        for _ in range(gap - 1):
                            sequence.append(None)  # Joker placeholder
                            available_jokers -= 1
                        sequence.append(sorted_cards[j])
                    else:
                        break

                    if len(sequence) >= 4:
                        return True

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
        """Obtiene una seguidilla válida"""
        for use_alt_values in [False, True]:
            value_list = ALT_VALUES if use_alt_values else VALUES
            sequence = self._get_sequence_with_values(value_list)
            if sequence:
                return sequence
        return None

    def _get_sequence_with_values(self, value_list):
        suits = {}
        for card in self.hand:
            if card.is_joker:
                continue
            if card.suit not in suits:
                suits[card.suit] = []
            suits[card.suit].append(card)

        jokers = [card for card in self.hand if card.is_joker]

        def circular_index_diff(a, b):
            """Devuelve la diferencia circular entre dos valores"""
            i_a = value_list.index(a)
            i_b = value_list.index(b)
            return (i_b - i_a) % len(value_list)

        for suit, cards in suits.items():
            sorted_cards = sorted(cards, key=lambda c: value_list.index(c.value))
            best_sequence = []

            for i in range(len(sorted_cards)):
                sequence = [sorted_cards[i]]
                available_jokers = jokers.copy()

                for j in range(i + 1, len(sorted_cards)):
                    prev_val = sequence[-1].value
                    curr_val = sorted_cards[j].value
                    gap = circular_index_diff(prev_val, curr_val)

                    if gap == 1:
                        sequence.append(sorted_cards[j])
                    elif gap > 1 and len(available_jokers) >= (gap - 1):
                        for _ in range(gap - 1):
                            sequence.append(available_jokers.pop(0))
                        sequence.append(sorted_cards[j])
                    else:
                        break

                    if len(sequence) >= 4 and len(sequence) > len(best_sequence):
                        best_sequence = sequence.copy()

                if len(sequence) + len(available_jokers) >= 4 and len(sequence) + len(available_jokers) > len(best_sequence):
                    while len(sequence) < 4 and available_jokers:
                        sequence.append(available_jokers.pop(0))
                    best_sequence = sequence

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


    @staticmethod
    def is_trio(cards):
        if len(cards) != 3:
            return False

        non_jokers = [card for card in cards if not card.is_joker]

        # No se permite trío de solo jokers
        if not non_jokers:
            return False

        base_value = non_jokers[0].value
        for card in non_jokers:
            if card.value != base_value:
                return False

        return True

    @staticmethod
    def is_sequence(cards):
        """Verifica si las cartas forman una seguidilla (4+ del mismo palo, consecutivas, con jokers permitidos)"""
        if len(cards) < 4:
            return False

        non_jokers = [c for c in cards if not c.is_joker]
        jokers = [c for c in cards if c.is_joker]

        if not non_jokers:
            return False

        suits = [c.suit for c in non_jokers]
        if len(set(suits)) != 1:
            return False  # Todos deben ser del mismo palo

        suit = suits[0]
        values = sorted(set(VALUES.index(c.value) for c in non_jokers))

        needed_jokers = 0
        for i in range(1, len(values)):
            gap = values[i] - values[i - 1]
            if gap == 0:
                return False  # Carta repetida no válida
            elif gap > 1:
                needed_jokers += gap - 1

        return needed_jokers <= len(jokers)