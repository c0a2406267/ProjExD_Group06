import pygame 
import math
import random
import time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("画像付きプレイヤーゲーム")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)

FONT = pygame.font.SysFont(None, 36)
FONT_JP = pygame.font.SysFont("meiryo", 80)
FONT_JP_SMALL = pygame.font.SysFont("meiryo", 40)

class SoundManager():
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.music.load("sounds/maou_bgm.mp3")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

        self.launch_sound = pygame.mixer.Sound("sounds/maou_launch.wav")
        self.launch_sound.set_volume(0.5)

        self.hit_sound = pygame.mixer.Sound("sounds/maou_hit.wav")
        self.hit_sound.set_volume(0.5)

        self.wall_hit_sound = pygame.mixer.Sound("sounds/maou_wall.wav")
        self.wall_hit_sound.set_volume(0.7)

    def play_launch(self):
        self.launch_sound.play()

    def play_hit(self):
        self.hit_sound.play()

    def play_wall_hit(self):
        self.wall_hit_sound.play()

sound_manager = SoundManager()

player_img = pygame.image.load("fig/0.png").convert_alpha()
default_img = pygame.transform.scale(player_img, (40, 40))
bg_img = pygame.image.load("fig/222_bg.png").convert_alpha()

class HPBar:
    def __init__(self, max_hp):
        self.max_hp = max_hp
        self.hp = max_hp
        self.width = 40
        self.height = 6

    def draw(self, screen, center_pos, enemy_radius):
        hp_ratio = self.hp / self.max_hp
        bar_x = center_pos[0] - self.width // 2
        bar_y = center_pos[1] + enemy_radius + 5

        pygame.draw.rect(screen, (150, 150, 150), (bar_x, bar_y, self.width, self.height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(self.width * hp_ratio), self.height))

    def take_damage(self, amount=1):
        self.hp = max(0, self.hp - amount)

    def is_dead(self):
        return self.hp <= 0

explosion_img = pygame.image.load("fig/explosion.gif").convert_alpha()
explosion_img = pygame.transform.scale(explosion_img, (500, 500))

player_pos = [150, 300]
player_radius = 20
player_vel = [0, 0]
dragging = False
launched = False
hit_enemies = set()
player_hp = HPBar(10)

enemy_radius = 25
enemies = []
max_enemies = 5
enemy_spawn_timer = 0
enemy_spawn_delay = 90

FRICTION = 0.98
attack_font = pygame.font.SysFont("MS Gothic", 48, bold=True)

score = 0

hamehameha_active = False
hame_timer = 0

explosions = pygame.sprite.Group()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.frame = 0

    def update(self):
        self.frame += 1
        if self.frame > 30:
            self.kill()

action_count = 0
enemy_attack_interval = 3

def distance(p1, p2):
    if isinstance(p2, dict) and "pos" in p2:
        p2 = p2["pos"]
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def keep_player_in_screen():
    hit = False
    if player_pos[0] - player_radius < 0:
        player_pos[0] = player_radius
        player_vel[0] *= -1
        hit = True
    elif player_pos[0] + player_radius > WIDTH:
        player_pos[0] = WIDTH - player_radius
        player_vel[0] *= -1
        hit = True

    if player_pos[1] - player_radius < 0:
        player_pos[1] = player_radius
        player_vel[1] *= -1
        hit = True
    elif player_pos[1] + player_radius > HEIGHT:
        player_pos[1] = HEIGHT - player_radius
        player_vel[1] *= -1
        hit = True

    if hit:
        sound_manager.play_wall_hit()

    return hit

def draw():
    screen.blit(bg_img, (0, 0))

    if dragging:
        pygame.draw.line(screen, GREEN, player_pos, pygame.mouse.get_pos(), 3)

    if player_hp.is_dead():
        show_game_over()
        pygame.quit()
        exit()

    rect = default_img.get_rect(center=(int(player_pos[0]), int(player_pos[1])))
    screen.blit(default_img, rect)
    enemy.draw()
    player_hp.draw(screen, player_pos, player_radius)

    score_text = f"Score: {score}"
    score_surf = pygame.font.SysFont(None, 36).render(score_text, True, WHITE)
    screen.blit(score_surf, (20, 20))

    explosions.draw(screen)
    explosions.update()

    if hamehameha_active:
        text = FONT.render("DOKKA-N", True, RED)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, text_rect)

    pygame.display.flip()

def show_game_over():
    blackout = pygame.Surface((WIDTH, HEIGHT))
    blackout.fill((0, 0, 0))
    blackout.set_alpha(180)
    screen.blit(blackout, (0, 0))

    text_surface = FONT_JP.render("ゲームオーバー", True, (255, 0, 0))
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text_surface, text_rect)

    pygame.display.update()
    time.sleep(5)

def show_start_screen():
    screen.fill(BLACK)

    title_surface = FONT_JP.render("ゲームスタート", True, WHITE)
    title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(title_surface, title_rect)

    start_surface = FONT_JP_SMALL.render("クリックしてスタート", True, WHITE)
    start_rect = start_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    screen.blit(start_surface, start_rect)

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

show_start_screen()

class Enemy():
    def __init__(self):
        self.enemies = []
        self.p = []
        self.spawn_timer = 0
        self.spawn_delay = 90
        self.max_enemies = 5
        self.radius = 20
        self.img = pygame.image.load(f"fig/enemy1.png")
        self.img = pygame.transform.scale(self.img, (80, 71))

    def fire_p(self, enemy):
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * 5
            vy = math.sin(angle) * 5
            self.p.append({'pos': list(enemy), 'vel': [vx, vy]})

    def fire_all(self):
        for e in self.enemies:
            self.fire_p(e)

    def update(self):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay and len(self.enemies) < self.max_enemies:
            x = random.randint(WIDTH // 2, WIDTH - self.radius)
            y = random.randint(self.radius, HEIGHT - self.radius)
            self.enemies.append([x, y, 5, HPBar(5)])
            self.spawn_timer = 0

        for b in self.p:
            b['pos'][0] += b['vel'][0]
            b['pos'][1] += b['vel'][1]
        self.p = [b for b in self.p if 0 <= b['pos'][0] <= WIDTH and 0 <= b['pos'][1] <= HEIGHT]

    def draw(self):
        for e in self.enemies:
            x, y, hp, hp_bar = e
            hp_bar.hp = hp
            hp_bar.draw(screen, (x, y), self.radius)
            rect = self.img.get_rect(center=(x, y))
            screen.blit(self.img, rect)
        for b in self.p:
            pygame.draw.circle(screen, RED, (int(b['pos'][0]), int(b['pos'][1])), 5)

    def check_collision(self, player_pos, player_radius):
        global score
        for e in self.enemies[:]:
            x, y, hp, hp_bar = e
            if distance(player_pos, (x, y)) <= player_radius + self.radius:
                e[2] -= 1
                if e[2] <= 0:
                    self.enemies.remove(e)
                    score += 1
                    sound_manager.play_hit()

running = True
enemy = Enemy()

while running:
    clock.tick(60)
    enemy.update()
    enemy_spawn_timer += 1

    if enemy_spawn_timer >= enemy_spawn_delay and len(enemies) < max_enemies:
        x = random.randint(WIDTH // 2, WIDTH - enemy_radius)
        y = random.randint(enemy_radius, HEIGHT - enemy_radius)
        enemies.append({"pos": [x, y], "hp_obj": HPBar(3)})
        enemy_spawn_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not dragging:
            mx, my = pygame.mouse.get_pos()
            if distance((mx, my), player_pos) <= player_radius:
                dragging = True

        if event.type == pygame.MOUSEBUTTONUP and dragging:
            mx, my = pygame.mouse.get_pos()
            dx = player_pos[0] - mx
            dy = player_pos[1] - my
            player_vel = [dx / 5, dy / 5]
            dragging = False
            launched = True
            sound_manager.play_launch()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not hamehameha_active and score >= 5:
                hamehameha_active = True
                hame_timer = 30
                explosions.add(Explosion(player_pos[:], explosion_img))
                enemy.enemies.clear()
                score -= 5

    if hamehameha_active:
        hame_timer -= 1 
        if hame_timer <= 0:
            hamehameha_active = False
    
    
    for b in enemy.p[:]:
        if distance(player_pos, b['pos']) <= player_radius + 5:
            player_hp.take_damage(1)
            enemy.p.remove(b)

    if launched:
        player_pos[0] += player_vel[0]
        player_pos[1] += player_vel[1]
        player_vel[0] *= FRICTION
        player_vel[1] *= FRICTION
        keep_player_in_screen()
        enemy.check_collision(player_pos, player_radius)

        for e in enemies[:]:
            enemy_id = id(e)
            if enemy_id not in hit_enemies and distance(player_pos, e["pos"]) <= player_radius + enemy_radius:
                hit_enemies.add(enemy_id)
                e["hp_obj"].take_damage()
                if e["hp_obj"].is_dead():
                    enemies.remove(e)
                    score += 1

        for b in enemy.p[:]:
            if distance(player_pos, b['pos']) <= player_radius + 5:
                player_hp.take_damage(1)
                enemy.p.remove(b)

        if math.hypot(player_vel[0], player_vel[1]) < 0.5:
            launched = False
            player_vel = [0, 0]
            hit_enemies.clear()

            action_count += 1

            if action_count >= enemy_attack_interval:
                attack_text = attack_font.render("敵の攻撃！", True, RED)
                screen.blit(attack_text, (WIDTH // 2 - attack_text.get_width() // 2, HEIGHT // 2 - 24))
                pygame.display.flip()
                pygame.time.wait(1000)
                enemy.fire_all()
                action_count = 0

    draw()

pygame.quit()