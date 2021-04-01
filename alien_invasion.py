import sys
from time import sleep

import pygame

from button import Button
from game_stats import GameStats
from scoreboard import Scoreboard
from random import randint
from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from star import Star


class AlienInvasion:
    """Ogólna klasa przeznaczona do zarządzania zasobami i sposobem działania gry."""

    def __init__(self):
        """Inicjalizacja gry i utworzenie jej zasobów."""
        pygame.init()
        self.settings = Settings()
        self.screen = self._screen_mode()

        pygame.display.set_caption("Inwazja Obcych")

        # Utworzenie egzemplarza przechowującego dane statystyczne dotyczące gry.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.stars = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_sky()
        self._create_fleet()

        # Utworzenie przycisków.
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Rozpoczęcie pętli głównej gry."""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._sky_update()
            self._update_screen()

    def _check_events(self):
        """Reakcja na zdarzenia generowane przez klawiaturę i mysz."""
        # Oczekiwanie na naciśnięcie klawisza lub przycisku myszy.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_play_button(self, mouse_pos):
        """Rozpoczęcie nowej gry po kliknięciu przycisku Gra przez użytkownika."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.settings.initialize_dynamic_settings()
            self._start_game()

            # Wyzerowanie danych statystycznych gry.
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

    def _start_game(self):
        # Zresetowanie statystyk i uruchomienie gry.
        self.stats.reset_stats()
        self.stats.game_active = True

        # Usunięcie zawartości list aliens i bullets.
        self.aliens.empty()
        self.bullets.empty()

        # Utworzenie nowej floty i wyśrodkowanie statku.
        self._create_fleet()
        self.ship.center_ship()

        # Ukrycie kursora myszy.
        pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Reakcja na wciśnięcie klawisza."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        if event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        if event.key == pygame.K_UP:
            self.ship.moving_up = True
        if event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        if event.key == pygame.K_q:
            sys.exit()
        if event.key == pygame.K_SPACE:
            self._fire_bullet()
        if event.key == pygame.K_g and self.stats.game_active == False:
            self._start_game()

    def _check_keyup_events(self, event):
        """Reakcja na zwolnienie klawisza."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        if event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        if event.key == pygame.K_UP:
            self.ship.moving_up = False
        if event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _screen_mode(self):
        """Wybór trybu wyświetlania - okno/pełny ekran."""
        if self.settings.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.settings.screen_width = self.screen.get_rect().width
            self.settings.screen_height = self.screen.get_rect().height
        else:
            self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        return self.screen

    def _fire_bullet(self):
        """Utworzenie nowego pocisku i dodanie go do grup pocisków."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Uaktualnienie położenia pocisków i usunięcie tych niewidocznych na ekranie."""
        # Uaktualnienie położenia pocisków.
        self.bullets.update()

        # Usunięcie pocisków, które wylecą poza ekran.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Reakcja na kolizję między pociskiem i obcym."""
        # Usunięcie wszystkich pocisków i obcych, między którymi doszło do kolizji.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # Pozbycie się istniejących pocisków, przyspieszenie gry i utworzenie nowej floty.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Inkrementacja numeru poziomu.
            self.stats.level += 1
            self.sb.prep_level()

    def _ship_hit(self):
        """Reakcja na uderzenie obcego w statek."""
        if self.stats.ships_left > 0:
            # Zmniejszenie wartości przechowywanej w ships_left.
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # Usunięcie zawartości list aliens i bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Utworzenie nowej floty i wyśrodkowanie statku.
            self._create_fleet()
            self.ship.center_ship()

            # Pauza na odpoczynek.
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _update_aliens(self):
        """Uaktualnienie położenia wszystkich obcych we flocie."""
        self._check_fleet_edges()
        self.aliens.update()

        # Wykrywanie kolizji pomiędzy statkiem, a obcym.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._update_screen()
            self._ship_hit()

        # Wyszukiwanie obcych docierających do dolnej krawędzi ekranu.
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        """Sprawdzanie czy jakiś obcy dotarł do dolnej krawędzi ekranu."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._update_screen()
                self._ship_hit()
                break

    def _create_sky(self):
        """Utworzenie gwiazd składających się na niebo."""
        star = Star(self)
        star_width, star_height = star.rect.size
        number_rows = self.settings.screen_height // star_height
        number_columns = self.settings.screen_width // star_width
        stars_amount = number_columns * number_rows // 4
        for x in range(stars_amount):
            self._create_star()

    def _create_star(self):
        """Utworzenie gwiazdy."""
        star = Star(self)
        star.rect.centerx = randint(1, self.settings.screen_width)
        star.rect.centery = randint(1, self.settings.screen_height)
        self.stars.add(star)

    def _check_star_edges(self):
        """Sprawdzenie czy gwiazda zniknęła za ekranem i przeniesienie jez z powrotem na górę ekranu."""
        screen_bottom = self.screen.get_height()
        for star in self.stars.sprites():
            if star.rect.top >= screen_bottom:
                star.rect.bottom = 0
                star.rect.x = randint(1, self.settings.screen_width)

    def _sky_update(self):
        self._check_star_edges()
        self.stars.update()

    def _create_fleet(self):
        """Utworzenie pełnej floty obcych."""
        # Utworzenie obcego i ustalenie liczby obcych, którzy zmieszczą się w rzędzie.
        # Odległość między poszczególnymi obcymi jest równa szerokości obcego.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        # Ustalenie ile rzędów zmieści się na ekranie.
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)
        if number_rows > 5:
            number_rows = 5

        # Utworzenie pełnej floty obcych.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 1.3 * alien_height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Odpowiednia eakcja, gdy obcy dotrze do krawędzi ekranu."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Przesunięcie całej floty w dół i zmiana kierunku, w którym się ona porusza."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.alien_fleet_drop_speed * self.settings.alien_fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        # Odświeżenie ekranu w trakcie każdej iteracji pętli.
        self.screen.fill(self.settings.bg_color)
        self.stars.draw(self.screen)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # Wyświetlenie infomacji o punktacji.
        self.sb.show_score()

        # Wyświetlenie przycisku tylko wtedy, gdy gra jest nieaktywna.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Wyświetlenie ostatnio zmodyfikowaniego ekranu.
        pygame.display.flip()


if __name__ == '__main__':
    # Utworzenie egzemplarza gry i jej uruchomienie.
    ai = AlienInvasion()
    ai.run_game()
