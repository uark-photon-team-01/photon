from dataclasses import dataclass, field
from typing import List # Just makes to code easier to read when declaring new Lists


@dataclass # dataclasses allow you write "data - only classes", that way you can declare fields and python writes "init" for you.
class PlayerData:
    playerID: int
    codename: str
    equipmentID: int
    team: str
    score: int = 0
    has_baseIcon: bool = False


@dataclass
class Game_State:  # field(default_factory=list) makes sure that every new instance of GameState gets it's own list
    redTeam: List[PlayerData] = field(default_factory=list)  # Team rosters
    greenTeam: List[PlayerData] = field(default_factory=list) # Typical lists like [] are shared across multiple instances in Python

    phase: str = "Beginning" # What screen/phase the player is in
    time_remaining: int = 0 # Time Left
    eventLog: List[str] = field(default_factory=list)

    # timer support
    timer_running: bool = False


if __name__ == "__main__":
    gs = Game_State()
    print("This model works. Yay! The game is currently in the", gs.phase, "phase.")
