# game/player.py

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []                 
        self.melds = []        
        self.points = 0                     
        self.has_gone_down = False
        
    def draw_card(self, card):
        self.hand.append(card)    
    
    def discard_card(self, card):
        if card in self.hand:
            self.hand.remove(card)
            return card
        else:
            return False
        
    def is_valid_meld(self, cards):
        if len(cards) < 3:
            return False

        jokers = [c for c in cards if c.rank.upper() == "JOKER"]
        non_jokers = [c for c in cards if c.rank.upper() != "JOKER"]

        if len(jokers) > 1:
            return False

        return self.is_trio(non_jokers) or self.is_ladder(non_jokers, jokers)

    def is_trio(self, cards):
    
        if not cards:
            return False
        ranks = [c.rank for c in cards]
        return len(set(ranks)) == 1

    def is_ladder(self, cards, jokers):
   
        if len(cards) + len(jokers) < 4:
            return False

        suits = [c.suit for c in cards]
        if len(set(suits)) > 1:
            return False  

        cards_sorted = sorted(cards, key=lambda c: c.numeric_value())
        expected = cards_sorted[0].numeric_value()
        gaps = 0

        for i in range(1, len(cards_sorted)):
            current = cards_sorted[i].numeric_value()
            diff = current - expected
            if diff == 1:
                expected = current
            elif diff > 1:
                gaps += diff - 1
                expected = current
            else:
                return False 

        return gaps <= len(jokers)
    
    def card_value(self, card):
        value_map = {
        '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 5, '8': 5, '9': 5,
        '10': 10, 'J': 10, 'Q': 10, 'K': 10,
        'A': 15, 'JOKER': 25
        }

        return value_map.get(card.rank.upper(), 0)
    
    def reset_for_new_round(self):
        self.hand.clear()
        self.melds.clear()
        self.has_gone_down = False