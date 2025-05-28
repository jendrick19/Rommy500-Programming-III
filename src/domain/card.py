from enum import Enum

class Suit(Enum):
    HEARTS = "♥" 
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"
    JOKER = "JOKER"

class Card:
    def __init__(self, rank, suit=None):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        if self.rank == Rank.JOKER:
            return "🃏"
        return f"{self.rank.value}{self.suit.value}"

    def value(self):
        """Devuelve el valor en puntos de la carta (puedes adaptarlo según el juego)."""
        if self.rank in {Rank.JACK, Rank.QUEEN, Rank.KING}:
            return 10
        if self.rank == Rank.ACE:
            return 11
        if self.rank == Rank.JOKER:
            return 0
        return int(self.rank.value)