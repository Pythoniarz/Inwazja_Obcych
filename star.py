import pygame
from pygame.sprite import Sprite


class Star(Sprite):
    """Klasa przedstawiająca jedną gwiazdę w grze."""

    def __init__(self, ai_game):
        """Inicjalizacja gwiazdy i jej położenie początkowe."""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings


        # Wczytanie obrazu gwiazdy i pobranie jej prostokąta.
        self.image = pygame.image.load('images/starro.png')
        self.rect = self.image.get_rect()

    def update(self):
        """Ruch gwiazdy w dół ekranu."""
        self.rect.bottom += self.settings.sky_speed




