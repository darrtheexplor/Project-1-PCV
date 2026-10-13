
import pygame
import sys
import random

pygame.init()

# Ukuran layar
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tennis Color Glove")

# Warna
BACKGROUND = (25, 30, 40)
COURT = (55, 145, 100)
WHITE = (255, 255, 255)
RED = (230, 70, 80)
BLUE = (70, 150, 240)
YELLOW = (255, 230, 80)

font = pygame.font.SysFont("Arial", 28)
small_font = pygame.font.SysFont("Arial", 18)
clock = pygame.time.Clock()

# Batas lapangan
LEFT, RIGHT = 80, 920
TOP, BOTTOM = 100, 530

# Pemain
player1 = pygame.Rect(150, 300, 35, 80)
player2 = pygame.Rect(815, 300, 35, 80)
PLAYER_SPEED = 5

# Bola
ball_x, ball_y = 500.0, 300.0
ball_radius = 12
ball_speed_x = random.choice([-4, 4])
ball_speed_y = random.choice([-3, 3])

# Skor
score1 = 0
score2 = 0


def reset_ball(direction):
    global ball_x, ball_y, ball_speed_x, ball_speed_y

    ball_x = WIDTH / 2
    ball_y = HEIGHT / 2
    ball_speed_x = 4 * direction
    ball_speed_y = random.choice([-3, -2, 2, 3])


running = True

while running:
    clock.tick(60)

    # Event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Kontrol keyboard
    keys = pygame.key.get_pressed()

    # Pemain kiri: WASD
    if keys[pygame.K_w]:
        player1.y -= PLAYER_SPEED
    if keys[pygame.K_s]:
        player1.y += PLAYER_SPEED
    if keys[pygame.K_a]:
        player1.x -= PLAYER_SPEED
    if keys[pygame.K_d]:
        player1.x += PLAYER_SPEED

    # Pemain kanan: tombol panah
    if keys[pygame.K_UP]:
        player2.y -= PLAYER_SPEED
    if keys[pygame.K_DOWN]:
        player2.y += PLAYER_SPEED
    if keys[pygame.K_LEFT]:
        player2.x -= PLAYER_SPEED
    if keys[pygame.K_RIGHT]:
        player2.x += PLAYER_SPEED

    # Batasi pemain di area masing-masing
    player1.clamp_ip(pygame.Rect(LEFT, TOP, 390, BOTTOM - TOP))
    player2.clamp_ip(pygame.Rect(510, TOP, 390, BOTTOM - TOP))

    # Gerakkan bola
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Pantulan atas dan bawah
    if ball_y - ball_radius <= TOP or ball_y + ball_radius >= BOTTOM:
        ball_speed_y *= -1

    # Tabrakan dengan pemain
    ball_rect = pygame.Rect(
        int(ball_x - ball_radius),
        int(ball_y - ball_radius),
        ball_radius * 2,
        ball_radius * 2
    )

    if ball_rect.colliderect(player1) and ball_speed_x < 0:
        ball_speed_x *= -1
        ball_x = player1.right + ball_radius

    if ball_rect.colliderect(player2) and ball_speed_x > 0:
        ball_speed_x *= -1
        ball_x = player2.left - ball_radius

    # Bola keluar lapangan = skor
    if ball_x < LEFT:
        score2 += 1
        reset_ball(1)

    elif ball_x > RIGHT:
        score1 += 1
        reset_ball(-1)

    # Gambar latar dan lapangan
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, COURT, (LEFT, TOP, RIGHT - LEFT, BOTTOM - TOP))

    # Garis lapangan dan net
    pygame.draw.rect(screen, WHITE, (120, 140, 760, 350), 3)
    pygame.draw.line(screen, WHITE, (500, TOP), (500, BOTTOM), 4)

    # Pemain dan bola
    pygame.draw.rect(screen, RED, player1, border_radius=8)
    pygame.draw.rect(screen, BLUE, player2, border_radius=8)
    pygame.draw.circle(screen, YELLOW, (int(ball_x), int(ball_y)), ball_radius)

    # Skor
    score_text = font.render(f"{score1}     -     {score2}", True, WHITE)
    screen.blit(score_text, (430, 35))

    # Petunjuk
    info = small_font.render("Player 1: WASD | Player 2: Arrow Keys", True, WHITE)
    screen.blit(info, (325, 555))

    pygame.display.flip()

pygame.quit()
sys.exit()
