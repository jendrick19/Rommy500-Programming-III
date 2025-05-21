import random
from card import Card, Suit, Rank

class Deck:
    def __init__(self, num_decks=1, include_jokers=False):
        self.cards = []
        for _ in range(num_decks):
            for suit in Suit:
                for rank in Rank:
                    if rank != Rank.JOKER:
                        self.cards.append(Card(rank, suit))
            if include_jokers:
                self.cards.append(Card(Rank.JOKER))
                self.cards.append(Card(Rank.JOKER))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

    def __len__(self):
        return len(self.cards)
