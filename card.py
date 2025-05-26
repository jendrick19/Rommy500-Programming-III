import random
from constants import SUITS, VALUES, CARD_VALUES

class Card:
    def __init__(self, value, suit=None):
        self.value = value
        self.suit = suit
        self.is_joker = (value == 'JOKER')
        self.face_up = False
        
        # Calcular el valor en puntos de la carta
        if self.is_joker:
            self.points = CARD_VALUES['JOKER']
        else:
            self.points = CARD_VALUES[value]
    
    def __str__(self):
        if self.is_joker:
            return "🃏"
        return f"{self.value}{self.suit}"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        if self.is_joker or other.is_joker:
            return False
        return self.value == other.value and self.suit == other.suit
    
    def flip(self):
        self.face_up = not self.face_up
        
    def to_dict(self):
        # Convertir los palos a códigos seguros para JSON
        suit_map = {
            '♠': 'S',
            '♥': 'H',
            '♦': 'D',
            '♣': 'C',
            None: ''
        }
        
        safe_suit = suit_map.get(self.suit, '')
        
        # Asegurarse de que todos los valores son serializables
        return {
            'value': str(self.value) if self.value else "",
            'suit': safe_suit,
            'is_joker': bool(self.is_joker),
            'face_up': bool(self.face_up),
            'points': int(self.points)
        }
    
    @staticmethod
    def from_dict(data):
        # Convertir los códigos seguros de vuelta a palos Unicode
        suit_map = {
            'S': '♠',
            'H': '♥',
            'D': '♦',
            'C': '♣',
            '': None
        }
        
        value = data['value']
        suit = suit_map.get(data['suit'], data['suit'])
        
        card = Card(value, suit)
        card.is_joker = bool(data['is_joker'])
        card.face_up = bool(data['face_up'])
        card.points = int(data['points'])
        return card
    
    def __hash__(self):
        return hash((self.value, self.suit, self.is_joker))

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.value == other.value and self.suit == other.suit and self.is_joker == other.is_joker


class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        self.cards = []
        # Crear las 52 cartas estándar
        for suit in SUITS:
            for value in VALUES:
                self.cards.append(Card(value, suit))
        
        # Añadir un Joker
        self.cards.append(Card('JOKER'))
        self.cards.append(Card('JOKER'))
        
        
        # Barajar
        self.shuffle()
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal(self, num_cards=1):
        if num_cards > len(self.cards):
            return []
        
        dealt_cards = []
        for _ in range(num_cards):
            card = self.cards.pop()
            card.face_up = True
            dealt_cards.append(card)
        
        return dealt_cards if num_cards > 1 else dealt_cards[0]
    
    def __len__(self):
        return len(self.cards)
    
    def to_dict(self):
        return {
            'cards': [card.to_dict() for card in self.cards]
        }
    
    @staticmethod
    def from_dict(data):
        deck = Deck()
        deck.cards = [Card.from_dict(card_data) for card_data in data['cards']]
        return deck

class DiscardPile:
    def __init__(self):
        self.cards = []
    
    def add(self, card):
        card.face_up = True
        self.cards.append(card)
    
    def take(self):
        if not self.cards:
            return None
        return self.cards.pop()
    
    def peek(self):
        if not self.cards:
            return None
        return self.cards[-1]
    
    def __len__(self):
        return len(self.cards)
    
    def to_dict(self):
        return {
            'cards': [card.to_dict() for card in self.cards]
        }
    
    @staticmethod
    def from_dict(data):
        pile = DiscardPile()
        pile.cards = [Card.from_dict(card_data) for card_data in data['cards']]
        return pile
