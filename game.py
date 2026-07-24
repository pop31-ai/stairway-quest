import pygame
import random
import sys
import os
import math
import traceback

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game.log")

def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass

try:
    log("=== START ===")
    pygame.init()

    WIDTH, HEIGHT = 800, 600
    FPS = 60

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Лесенки: Путь наверх")
    clock = pygame.time.Clock()

    WHITE = (255, 255, 255)
    BLACK = (30, 30, 30)
    GREEN = (60, 180, 75)
    DARK_GREEN = (40, 130, 55)
    BLUE = (70, 130, 200)
    LIGHT_BLUE = (135, 200, 255)
    BROWN = (140, 100, 50)
    DARK_BROWN = (100, 70, 30)
    YELLOW = (255, 215, 0)
    RED = (220, 50, 50)
    GRAY = (180, 180, 180)
    DARK_GRAY = (120, 120, 120)
    ORANGE = (240, 150, 30)
    SKY_TOP = (20, 20, 60)
    SKY_BOT = (50, 80, 140)
    ARROW_UP = (100, 255, 100)
    ARROW_DOWN = (255, 180, 80)
    ARROW_ALT = (150, 200, 255)

    font_small = pygame.font.SysFont("Arial", 20)
    font_med = pygame.font.SysFont("Arial", 32, bold=True)
    font_big = pygame.font.SysFont("Arial", 56, bold=True)

    log("Fonts OK")


    class Particle:
        def __init__(self, x, y, color, vx=0, vy=0, life=30, size=3):
            self.x = x
            self.y = y
            self.color = color
            self.vx = vx
            self.vy = vy
            self.life = life
            self.max_life = life
            self.size = size

        def update(self):
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.1
            self.life -= 1

        def draw(self, surf):
            alpha = self.life / self.max_life
            s = max(1, int(self.size * alpha))
            pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), s, s))

        def alive(self):
            return self.life > 0


    class Player:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.w = 24
            self.h = 32
            self.vx = 0
            self.vy = 0
            self.speed = 3.5
            self.jump_power = -9
            self.gravity = 0.45
            self.on_ground = False
            self.on_ladder = False
            self.facing = 1
            self.anim = 0
            self.lives = 3
            self.coins = 0
            self.stars = 0
            self.invincible = 0
            self.climb_anim = 0

        def rect(self):
            return pygame.Rect(self.x, self.y, self.w, self.h)

        def update(self, platforms, ladders):
            keys = pygame.key.get_pressed()
            self.on_ladder = False

            for lad in ladders:
                pr = self.rect()
                lr = lad.rect()
                if pr.colliderect(lr):
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        self.on_ladder = True
                        self.vy = -2.5
                        self.vx = 0
                        self.x = lr.centerx - self.w // 2
                    elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        self.on_ladder = True
                        self.vy = 2.5
                        self.vx = 0
                        self.x = lr.centerx - self.w // 2
                    elif abs(self.vy) < 1:
                        self.on_ladder = True
                        self.vy = 0

            if not self.on_ladder:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vx = -self.speed
                    self.facing = -1
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vx = self.speed
                    self.facing = 1
                else:
                    self.vx = 0

                if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
                    self.vy = self.jump_power
                    self.on_ground = False

                self.vy += self.gravity
            else:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vx = -self.speed * 0.5
                    self.facing = -1
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vx = self.speed * 0.5
                    self.facing = 1

            self.x += self.vx
            self._collide_x(platforms)
            self.y += self.vy
            self.on_ground = False
            self._collide_y(platforms)

            if self.y > HEIGHT + 100:
                self.die()
                return

            if self.invincible > 0:
                self.invincible -= 1

            self.anim += 0.15
            self.climb_anim += 0.1

        def _collide_x(self, platforms):
            pr = self.rect()
            for p in platforms:
                pr2 = p.rect()
                if pr.colliderect(pr2):
                    if self.vx > 0:
                        self.x = pr2.left - self.w
                    elif self.vx < 0:
                        self.x = pr2.right
                    self.vx = 0
                    pr = self.rect()

        def _collide_y(self, platforms):
            pr = self.rect()
            for p in platforms:
                pr2 = p.rect()
                if pr.colliderect(pr2):
                    if self.vy > 0:
                        self.y = pr2.top - self.h
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0 and not self.on_ladder:
                        self.y = pr2.bottom
                        self.vy = 0
                    pr = self.rect()

        def die(self):
            self.lives -= 1
            self.invincible = 90
            self.vy = 0
            self.y = HEIGHT - 80
            self.x = 40
            self.vx = 0
            log(f"Player died. Lives left: {self.lives}")
            return self.lives <= 0

        def draw(self, surf):
            if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
                return

            x, y = int(self.x), int(self.y)

            if self.on_ladder:
                leg_offset = int(self.climb_anim * 4) % 2
                pygame.draw.rect(surf, BLUE, (x + 4, y + 12, 16, 14))
                pygame.draw.rect(surf, LIGHT_BLUE, (x + 6, y + 14, 12, 10))
                pygame.draw.circle(surf, (255, 210, 170), (x + 12, y + 6), 7)
                pygame.draw.circle(surf, (50, 40, 30), (x + 12, y + 5), 6)
                pygame.draw.rect(surf, DARK_BROWN, (x + 6 + leg_offset * 3, y + 26, 5, 6))
                pygame.draw.rect(surf, DARK_BROWN, (x + 13 - leg_offset * 3, y + 26, 5, 6))
            else:
                walk = int(self.anim * 3) % 4
                leg_offset = [0, 2, 0, -2][walk] if self.on_ground and abs(self.vx) > 0.5 else 0

                pygame.draw.rect(surf, BLUE, (x + 4, y + 12, 16, 14))
                pygame.draw.rect(surf, LIGHT_BLUE, (x + 6, y + 14, 12, 10))

                pygame.draw.circle(surf, (255, 210, 170), (x + 12, y + 6), 7)
                pygame.draw.circle(surf, (50, 40, 30), (x + 12, y + 5), 6)

                eye_x = x + 12 + self.facing * 2
                pygame.draw.circle(surf, WHITE, (eye_x, y + 5), 2)
                pygame.draw.circle(surf, BLACK, (eye_x + self.facing, y + 5), 1)

                pygame.draw.rect(surf, DARK_BROWN, (x + 8, y + 26, 4, 6 + leg_offset))
                pygame.draw.rect(surf, DARK_BROWN, (x + 12, y + 26, 4, 6 - leg_offset))

                arm_y = y + 16 + int(self.anim * 2) % 3
                pygame.draw.rect(surf, (255, 210, 170), (x + 1, arm_y, 4, 8))
                pygame.draw.rect(surf, (255, 210, 170), (x + 19, arm_y, 4, 8))


    class Platform:
        def __init__(self, x, y, w, h, color=BROWN):
            self.rect_obj = pygame.Rect(x, y, w, h)
            self.color = color

        def rect(self):
            return self.rect_obj

        def draw(self, surf):
            r = self.rect_obj
            pygame.draw.rect(surf, self.color, r)
            pygame.draw.rect(surf, DARK_BROWN, r, 2)
            for i in range(r.left + 8, r.right - 4, 16):
                pygame.draw.line(surf, DARK_BROWN, (i, r.top + 4), (i + 8, r.top + 4), 1)


    class Ladder:
        def __init__(self, x, y, h, is_alt=False):
            self.rect_obj = pygame.Rect(x, y, 24, h)
            self.x = x
            self.y = y
            self.h = h
            self.is_alt = is_alt

        def rect(self):
            return self.rect_obj

        def draw(self, surf):
            x, y, h = self.x, self.y, self.h
            color = (150, 170, 200) if self.is_alt else GRAY
            dark_color = (110, 130, 160) if self.is_alt else DARK_GRAY
            pygame.draw.rect(surf, color, (x, y, 4, h))
            pygame.draw.rect(surf, color, (x + 20, y, 4, h))
            for i in range(y + 5, y + h - 2, 14):
                pygame.draw.rect(surf, color, (x + 4, i, 16, 3))
                pygame.draw.rect(surf, dark_color, (x + 4, i, 16, 3), 1)


    class Coin:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.r = 8
            self.anim = random.uniform(0, 6.28)
            self.collected = False

        def rect(self):
            return pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

        def update(self):
            self.anim += 0.08

        def draw(self, surf):
            if self.collected:
                return
            stretch = abs(int(self.r * abs(math.cos(self.anim))))
            s = max(stretch, 3)
            pygame.draw.ellipse(surf, YELLOW, (self.x - s, self.y - self.r, s * 2, self.r * 2))
            pygame.draw.ellipse(surf, ORANGE, (self.x - s, self.y - self.r, s * 2, self.r * 2), 2)


    class Star:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.anim = random.uniform(0, 6.28)
            self.collected = False

        def rect(self):
            return pygame.Rect(self.x - 10, self.y - 10, 20, 20)

        def update(self):
            self.anim += 0.05

        def draw(self, surf):
            if self.collected:
                return
            glow = int(3 * math.sin(self.anim))
            pts = []
            for i in range(5):
                angle = math.radians(-90 + i * 72)
                ox = math.cos(angle) * (10 + glow)
                oy = math.sin(angle) * (10 + glow)
                pts.append((self.x + ox, self.y + oy))
                angle2 = math.radians(-90 + i * 72 + 36)
                ox2 = math.cos(angle2) * (4 + glow // 2)
                oy2 = math.sin(angle2) * (4 + glow // 2)
                pts.append((self.x + ox2, self.y + oy2))
            pygame.draw.polygon(surf, YELLOW, pts)
            pygame.draw.polygon(surf, ORANGE, pts, 2)


    class Spike:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.w = 30
            self.h = 20

        def rect(self):
            return pygame.Rect(self.x, self.y - self.h, self.w, self.h)

        def draw(self, surf):
            pts = [
                (self.x, self.y),
                (self.x + self.w // 2, self.y - self.h),
                (self.x + self.w, self.y),
            ]
            pygame.draw.polygon(surf, RED, pts)
            pygame.draw.polygon(surf, (180, 30, 30), pts, 2)


    class Crate:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.w = 32
            self.h = 32
            self.anim = 0

        def rect(self):
            return pygame.Rect(self.x, self.y - self.h, self.w, self.h)

        def update(self):
            self.anim += 0.06

        def draw(self, surf):
            import math
            r = self.rect()
            pygame.draw.rect(surf, (160, 120, 50), r)
            pygame.draw.rect(surf, (120, 85, 30), r, 2)
            pygame.draw.line(surf, (120, 85, 30), (r.left, r.top), (r.right, r.bottom), 2)
            pygame.draw.line(surf, (120, 85, 30), (r.right, r.top), (r.left, r.bottom), 2)
            glow = int(4 * math.sin(self.anim))
            pygame.draw.circle(surf, YELLOW, (r.centerx, r.centery), max(2, 5 + glow))
            pygame.draw.circle(surf, ORANGE, (r.centerx, r.centery), max(2, 5 + glow), 2)


    def draw_arrow_up(surf, x, y, color, size=12, pulse=0):
        s = size + int(2 * math.sin(pulse))
        pts = [
            (x, y - s),
            (x - s // 2, y),
            (x - s // 4, y),
            (x - s // 4, y + s // 2),
            (x + s // 4, y + s // 2),
            (x + s // 4, y),
            (x + s // 2, y),
        ]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)


    def draw_arrow_down(surf, x, y, color, size=12, pulse=0):
        s = size + int(2 * math.sin(pulse))
        pts = [
            (x, y + s),
            (x - s // 2, y),
            (x - s // 4, y),
            (x - s // 4, y - s // 2),
            (x + s // 4, y - s // 2),
            (x + s // 4, y),
            (x + s // 2, y),
        ]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 1)


    def draw_arrow_hint(surf, x, y, direction, color, pulse):
        if direction == "up":
            draw_arrow_up(surf, x, y, color, 10, pulse)
        else:
            draw_arrow_down(surf, x, y, color, 10, pulse)


    def generate_level(level_num):
        platforms = []
        ladders = []
        coins = []
        stars = []
        spikes = []
        arrows = []

        prev_x = 0
        prev_w = WIDTH
        prev_y = HEIGHT - 40
        platforms.append(Platform(0, prev_y, WIDTH, 40))

        num_floors = min(4 + level_num, 10)

        for i in range(num_floors):
            fy = prev_y - 90
            fw = random.randint(140, 280)
            fx = random.randint(20, WIDTH - fw - 20)

            platforms.append(Platform(fx, fy, fw, 14, DARK_GREEN if i % 2 == 0 else GREEN))

            ol = max(fx, prev_x)
            or_ = min(fx + fw, prev_x + prev_w)

            if ol < or_ - 20:
                lx = random.randint(ol + 5, or_ - 25)
            else:
                mid = (prev_x + prev_w // 2 + fx + fw // 2) // 2
                mid = max(fx + 15, min(mid, fx + fw - 25))
                lx = mid

            ladder_h = prev_y - fy
            ladders.append(Ladder(lx, fy, ladder_h))
            arrows.append(("up", lx + 12, prev_y - 10))

            if level_num >= 2 and random.random() < 0.35 and i > 0:
                alt_fx = random.randint(20, WIDTH - fw - 20)
                alt_fw = random.randint(120, 200)
                platforms.append(Platform(alt_fx, fy, alt_fw, 14, DARK_GREEN if i % 2 == 0 else GREEN))

                aol = max(alt_fx, prev_x)
                aor_ = min(alt_fx + alt_fw, prev_x + prev_w)
                if aor_ - aol >= 30:
                    alx = random.randint(aol + 5, aor_ - 25)
                elif aor_ > aol:
                    alx = (aol + aor_) // 2
                else:
                    alx = alt_fx + alt_fw // 2

                ladders.append(Ladder(alx, fy, ladder_h, is_alt=True))
                arrows.append(("up", alx + 12, prev_y - 10))

                for _ in range(random.randint(1, 2)):
                    cx = random.randint(alt_fx + 10, alt_fx + alt_fw - 10)
                    coins.append(Coin(cx, fy - 16))

            for _ in range(random.randint(1, 3)):
                cx = random.randint(fx + 10, fx + fw - 10)
                cy = fy - 16
                coins.append(Coin(cx, cy))

            if random.random() < 0.3 + level_num * 0.05:
                sx = random.randint(fx + 10, fx + fw - 40)
                spikes.append(Spike(sx, prev_y - 4))

            if random.random() < 0.2:
                stx = random.randint(fx + 10, fx + fw - 10)
                sty = fy - 30
                stars.append(Star(stx, sty))

            prev_x = fx
            prev_w = fw
            prev_y = fy

        top_y = prev_y - 90
        door_x = random.randint(100, WIDTH - 130)
        door = Crate(door_x, top_y)
        top_plat = Platform(door_x - 40, top_y, 110, 14, BROWN)

        ol = max(top_plat.rect_obj.left, prev_x)
        or_ = min(top_plat.rect_obj.right, prev_x + prev_w)
        if ol >= or_:
            center = (prev_x + prev_w // 2)
            door_x = max(prev_x + 40, min(center, prev_x + prev_w - 70))
            top_plat = Platform(door_x - 40, top_y, 110, 14, BROWN)
            door = Crate(door_x, top_y)

        platforms.append(top_plat)

        ol2 = max(top_plat.rect_obj.left, prev_x)
        or2 = min(top_plat.rect_obj.right, prev_x + prev_w)
        if or2 - ol2 >= 30:
            lx_final = random.randint(ol2 + 5, or2 - 25)
        elif or2 > ol2:
            lx_final = (ol2 + or2) // 2
        else:
            lx_final = prev_x + prev_w // 2
        ladders.append(Ladder(lx_final, top_y, prev_y - top_y))
        arrows.append(("up", lx_final + 12, prev_y - 10))

        arrows.append(("up", door_x + 15, top_y - 20))

        log(f"Level {level_num}: {len(platforms)} platforms, {len(ladders)} ladders")

        return platforms, ladders, coins, stars, spikes, door, arrows


    def draw_sky(surf):
        for y in range(0, HEIGHT, 4):
            t = y / HEIGHT
            r = int(SKY_TOP[0] * (1 - t) + SKY_BOT[0] * t)
            g = int(SKY_TOP[1] * (1 - t) + SKY_BOT[1] * t)
            b = int(SKY_TOP[2] * (1 - t) + SKY_BOT[2] * t)
            pygame.draw.rect(surf, (r, g, b), (0, y, WIDTH, 4))


    def draw_stars_bg(surf, star_list):
        for sx, sy in star_list:
            brightness = random.randint(150, 255)
            pygame.draw.circle(surf, (brightness, brightness, brightness), (sx, sy), 1)


    def draw_hud(surf, player, level_num):
        lives_text = font_small.render(f"Жизни: {player.lives}", True, WHITE)
        coins_text = font_small.render(f"Монеты: {player.coins}", True, YELLOW)
        stars_text = font_small.render(f"Звёзды: {player.stars}", True, ORANGE)
        level_text = font_small.render(f"Уровень: {level_num}", True, WHITE)
        regen_text = font_small.render("R — новый уровень", True, GRAY)

        surf.blit(lives_text, (10, 10))
        surf.blit(coins_text, (10, 35))
        surf.blit(stars_text, (150, 10))
        surf.blit(level_text, (WIDTH - 130, 10))
        surf.blit(regen_text, (WIDTH - 180, 35))

        for i in range(player.lives):
            pygame.draw.polygon(surf, RED, [
                (20 + i * 25, HEIGHT - 25),
                (28 + i * 25, HEIGHT - 38),
                (36 + i * 25, HEIGHT - 25),
                (30 + i * 25, HEIGHT - 22),
                (24 + i * 25, HEIGHT - 22),
            ])


    bg_stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(80)]


    def main():
        log("main() started")
        state = "menu"
        level = 1
        score = 0
        particles = []

        platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
        player = Player(40, HEIGHT - 80)
        frame = 0
        lc_timer = 0

        while True:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        log("QUIT event")
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if state == "menu" and event.key == pygame.K_RETURN:
                            state = "playing"
                            level = 1
                            score = 0
                            platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
                            player = Player(40, HEIGHT - 80)
                            log("Game started")
                        elif state == "playing" and event.key == pygame.K_r:
                            platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
                            player.x = 40
                            player.y = HEIGHT - 80
                            player.vx = 0
                            player.vy = 0
                            log("Level regenerated")
                        elif state == "gameover" and event.key == pygame.K_RETURN:
                            state = "playing"
                            level = 1
                            score = 0
                            platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
                            player = Player(40, HEIGHT - 80)
                        elif state == "win" and event.key == pygame.K_RETURN:
                            state = "playing"
                            level = 1
                            score = 0
                            platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
                            player = Player(40, HEIGHT - 80)

                if state == "menu":
                    draw_sky(screen)
                    draw_stars_bg(screen, bg_stars)

                    title = font_big.render("ЛЕСЕНКИ", True, YELLOW)
                    sub = font_med.render("Путь наверх", True, WHITE)
                    hint = font_small.render("Нажми ENTER чтобы начать", True, GRAY)
                    controls = font_small.render("WASD / Стрелки — движение, SPACE — прыжок", True, GRAY)
                    controls2 = font_small.render("W/S — лесенка, R — новый уровень", True, GRAY)

                    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 160))
                    screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 230))
                    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 340))
                    screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, 390))
                    screen.blit(controls2, (WIDTH // 2 - controls2.get_width() // 2, 420))

                    pygame.display.flip()
                    clock.tick(FPS)
                    continue

                if state == "gameover":
                    draw_sky(screen)
                    draw_stars_bg(screen, bg_stars)

                    go = font_big.render("ИГРА ОКОНЧЕНА", True, RED)
                    sc = font_med.render(f"Счёт: {score}", True, YELLOW)
                    coins_t = font_small.render(f"Монеты собраны: {player.coins}", True, ORANGE)
                    stars_t = font_small.render(f"Звёзды собраны: {player.stars}", True, YELLOW)
                    lvl_t = font_small.render(f"Уровень: {level}", True, WHITE)

                    credits = [
                        ("ЛЕСЕНКИ: Путь наверх", YELLOW, font_med),
                        ("", WHITE, font_small),
                        ("Разработка", GRAY, font_small),
                        ("pop31", WHITE, font_med),
                        ("", WHITE, font_small),
                        ("Движок", GRAY, font_small),
                        ("Pygame 2.6", LIGHT_BLUE, font_small),
                        ("", WHITE, font_small),
                        ("Спасибо за игру!", GREEN, font_med),
                    ]

                    y_off = (frame * 1.2) % (HEIGHT + len(credits) * 40 + 200)

                    for i, (text, color, f) in enumerate(credits):
                        cy = int(HEIGHT - y_off + i * 40 + 100)
                        if -30 < cy < HEIGHT + 30:
                            t = f.render(text, True, color)
                            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, cy))

                    screen.blit(go, (WIDTH // 2 - go.get_width() // 2, 60))
                    screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 120))
                    screen.blit(coins_t, (WIDTH // 2 - coins_t.get_width() // 2, 155))
                    screen.blit(stars_t, (WIDTH // 2 - stars_t.get_width() // 2, 175))
                    screen.blit(lvl_t, (WIDTH // 2 - lvl_t.get_width() // 2, 195))

                    hint = font_small.render("ENTER — заново", True, GRAY)
                    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

                    pygame.display.flip()
                    clock.tick(FPS)
                    continue

                if state == "win":
                    draw_sky(screen)
                    draw_stars_bg(screen, bg_stars)

                    w = font_big.render("ПОБЕДА!", True, YELLOW)
                    sc = font_med.render(f"Итоговый счёт: {score}", True, WHITE)

                    credits = [
                        ("ЛЕСЕНКИ: Путь наверх", YELLOW, font_med),
                        ("", WHITE, font_small),
                        ("Ты прошёл все 11 уровней!", GREEN, font_med),
                        ("", WHITE, font_small),
                        (f"Монеты: {score // 10}", ORANGE, font_small),
                        ("", WHITE, font_small),
                        ("Разработка", GRAY, font_small),
                        ("pop31", WHITE, font_med),
                        ("", WHITE, font_small),
                        ("Движок", GRAY, font_small),
                        ("Pygame 2.6", LIGHT_BLUE, font_small),
                        ("", WHITE, font_small),
                        ("Спасибо за игру!", GREEN, font_med),
                        ("", WHITE, font_small),
                        ("THE END", GRAY, font_big),
                    ]

                    y_off = (frame * 1.0) % (HEIGHT + len(credits) * 40 + 200)

                    for i, (text, color, f) in enumerate(credits):
                        cy = int(HEIGHT - y_off + i * 40 + 100)
                        if -30 < cy < HEIGHT + 30:
                            t = f.render(text, True, color)
                            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, cy))

                    screen.blit(w, (WIDTH // 2 - w.get_width() // 2, 40))
                    screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 110))

                    hint = font_small.render("ENTER — заново", True, GRAY)
                    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

                    pygame.display.flip()
                    clock.tick(FPS)
                    continue

                if state == "level_complete":
                    lc_timer -= 1
                    draw_sky(screen)
                    draw_stars_bg(screen, bg_stars)
                    lc = font_med.render(f"Уровень {level - 1} пройден!", True, GREEN)
                    sc = font_med.render(f"Счёт: {score}", True, YELLOW)
                    screen.blit(lc, (WIDTH // 2 - lc.get_width() // 2, 220))
                    screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 280))
                    pygame.display.flip()
                    clock.tick(FPS)
                    if lc_timer <= 0:
                        platforms, ladders, coins, stars_list, spikes, door, arrows = generate_level(level)
                        player.x = 40
                        player.y = HEIGHT - 80
                        player.vx = 0
                        player.vy = 0
                        state = "playing"
                    continue

                player.update(platforms, ladders)

                if player.lives <= 0:
                    state = "gameover"
                    log("GAME OVER from fall")

                for c in coins:
                    c.update()
                    if not c.collected and player.rect().colliderect(c.rect()):
                        c.collected = True
                        player.coins += 1
                        score += 10
                        for _ in range(8):
                            particles.append(Particle(c.x, c.y, YELLOW,
                                                      random.uniform(-2, 2), random.uniform(-3, -1), 20, 4))

                for s in stars_list:
                    s.update()
                    if not s.collected and player.rect().colliderect(s.rect()):
                        s.collected = True
                        player.stars += 1
                        score += 50
                        for _ in range(12):
                            particles.append(Particle(s.x, s.y, ORANGE,
                                                      random.uniform(-3, 3), random.uniform(-4, -1), 30, 5))

                door.update()
                if player.rect().colliderect(door.rect()):
                    score += 200
                    level += 1
                    log(f"Door reached! Next level: {level}")
                    if level > 11:
                        state = "win"
                    else:
                        state = "level_complete"
                        lc_timer = 120

                for sp in spikes:
                    if player.invincible <= 0 and player.rect().colliderect(sp.rect()):
                        log(f"Spike hit! pos=({player.x:.0f},{player.y:.0f})")
                        dead = player.die()
                        for _ in range(10):
                            particles.append(Particle(player.x + 12, player.y + 16, RED,
                                                      random.uniform(-3, 3), random.uniform(-4, 0), 25, 5))
                        if dead:
                            state = "gameover"
                            log("GAME OVER")

                for p in particles[:]:
                    p.update()
                    if not p.alive():
                        particles.remove(p)

                draw_sky(screen)
                draw_stars_bg(screen, bg_stars)

                for p in platforms:
                    p.draw(screen)
                for l in ladders:
                    l.draw(screen)
                for c in coins:
                    c.draw(screen)
                for s in stars_list:
                    s.draw(screen)
                for sp in spikes:
                    sp.draw(screen)
                door.draw(screen)

                pulse = frame * 0.08
                for direction, ax, ay in arrows:
                    color = ARROW_UP if direction == "up" else ARROW_DOWN
                    draw_arrow_hint(screen, ax, ay, direction, color, pulse)

                player.draw(screen)

                for p in particles:
                    p.draw(screen)

                draw_hud(screen, player, level)

                pygame.display.flip()
                clock.tick(FPS)
                frame += 1

            except Exception as e:
                log(f"ERROR in loop: {e}")
                log(traceback.format_exc())
                pygame.quit()
                raise

    if __name__ == "__main__":
        main()

except Exception as e:
    log(f"FATAL: {e}")
    log(traceback.format_exc())
    raise
