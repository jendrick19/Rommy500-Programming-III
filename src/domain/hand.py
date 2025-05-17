class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def total_value(self):
        return sum(card.value() for card in self.cards)

    def __repr__(self):
        return f"Hand({', '.join(str(card) for card in self.cards)})"
