# Constantes de pantalla
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 700
FPS = 60

# Colores
BG_COLOR = (0, 100, 0)  # Verde oscuro para mesa de cartas
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 130, 180)
DISABLED_BUTTON_COLOR = (100, 100, 100)
CARD_BACK_COLOR = (25, 25, 112)
PLAYER_COLORS = [
    (255, 0, 0),    # Rojo
    (0, 0, 255),    # Azul
    (0, 255, 0),    # Verde
    (255, 255, 0),  # Amarillo
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cian
    (255, 165, 0),  # Naranja
    (128, 0, 128),  # Púrpura
    (165, 42, 42),  # Marrón
    (255, 192, 203),# Rosa
    (0, 128, 128),  # Verde azulado
    (128, 128, 0),  # Oliva
    (128, 0, 0)     # Granate
]
INPUT_ACTIVE_COLOR = (100, 100, 200)
INPUT_INACTIVE_COLOR = (70, 70, 70)

# Constantes de red
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096

# Constantes del juego
CARD_WIDTH = 75
CARD_HEIGHT = 100
CARD_SPACING = 18

# Valores de las cartas
CARD_VALUES = {
    '2': 5, '3': 5, '4': 5, '5': 5, '6': 5, '7': 5, '8': 5, '9': 5,
    '10': 10, 'J': 10, 'Q': 10, 'K': 10,
    'A': 15, 'JOKER': 25
}

# Palos
SUITS = ['♠', '♥', '♦', '♣']

# Valores
VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
ALT_VALUES = VALUES[1:] + ['A']  


# Rondas
ROUNDS = [
    "Un Trío y Una Seguidilla",
    "Dos Seguidillas",
    "Tres Tríos",
    "Una Seguidilla y Dos Tríos (Ronda Completa)"
]

# Estados del juego
GAME_STATE_WAITING = 0
GAME_STATE_PLAYING = 1
GAME_STATE_ROUND_END = 2
GAME_STATE_GAME_END = 3

# Acciones del jugador
ACTION_DRAW_DECK = 0
ACTION_DRAW_DISCARD = 1
ACTION_PLAY_COMBINATION = 2
ACTION_ADD_TO_COMBINATION = 3
ACTION_DISCARD = 4
ACTION_REPLACE_JOKER = 5
