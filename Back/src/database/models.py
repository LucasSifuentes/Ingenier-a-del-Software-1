from sqlalchemy import Column, ForeignKey, Integer, String, Text, Date
from .db import Base 

## --- ESTRUCTURAS BÁSICAS: User, Player y Lobby ---

class User(Base):
    """
    La cuenta permanente del usuario. Solo guarda información general.
    """
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(50), nullable=False)
    birthday = Column(Date,nullable=False)

class Player(Base):
    """
    El rol temporal de un User dentro de una partida.
    Conecta al User con el Lobby o el Game.
    """
    __tablename__ = 'players'
    player_id = Column(Integer, primary_key=True)
    player_name = Column(String(50), nullable=False)    
    user_id = Column(Integer, ForeignKey('users.user_id'))
    lobby_id = Column(Integer, ForeignKey('lobbies.lobby_id'), nullable=True)
    game_id = Column(Integer, ForeignKey('games.game_id'), nullable=True)

class Lobby(Base):
    """
    La sala de espera. Existe antes de que empiece un Game.
    """
    __tablename__ = 'lobbies'
    lobby_id = Column(Integer, primary_key=True)
    lobby_name = Column(String)
    player_amount = Column(Integer)
    lobby_owner = Column(Integer, ForeignKey('players.player_id'))
    max_players = Column(Integer)
    min_players = Column(Integer)


## --- ESTRUCTURAS DEL JUEGO: Game y PlayerState ESTO NO ESTA DEFINIDO, PUEDE CAMBIAR ---

class Game(Base):
    """
    La partida en sí. Contiene el estado general del juego.
    """
    __tablename__ = 'games'
    game_id = Column(Integer, primary_key=True)
    game_name = Column(String)
    player_order = Column(Text) # Guardaremos la lista de IDs de jugadores como texto. Ej: "10,12,11"
    current_turn = Column(Integer) # Guardamos el ID del jugador cuyo turno es
    main_deck = Column(Text) # Guardaremos la lista de cartas del mazo principal
    discard_deck = Column(Text) # La lista de cartas del mazo de descarte

class PlayerState(Base):
    """
    El estado específico de un jugador DENTRO de una partida.
    """
    __tablename__ = 'player_states'
    player_id = Column(Integer, ForeignKey('players.player_id'), primary_key=True)
    cards_in_hand = Column(Text) # Las cartas que el jugador tiene en la mano
    secret_cards = Column(Text) # Las cartas de secreto (ej: "Asesino", "Detective")

