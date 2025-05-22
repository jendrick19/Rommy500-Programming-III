# game/player.py

#from ..src.domain.hand import Hand
#from ..src.domain.card import Card

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = Hand()
        self.score = 0
        self.has_drawn = False

    def draw_card(self, source):
        card = source()
        if card:
            self.hand.add_card(card)
            self.has_drawn = True
        return card

    def discard(self, index):
        if 0 <= index < len(self.hand.cards):
            card = self.hand.cards.pop(index)
            self.has_drawn = False
            return card
        return None

    def discard_card(self, card):
        if card in self.hand.cards:
            self.hand.cards.remove(card)
            self.has_drawn = False
            return card
        return None

    def get_hand_value(self):
        return self.hand.total_value()

    def update_score(self, value):
        self.score += value

    def reset_hand(self):
        self.hand.clear()
        self.has_drawn = False

    def __repr__(self):
        return f"{self.name}: {self.hand} | Score: {self.score}"