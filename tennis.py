import pygame
import cv2
import numpy as np
import os

pygame.init()

# Ukuran game
W, H = 1000, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Tennis Game")
clock = pygame.time.Clock()

folder = os.path.dirname(os.path.abspath(__file__))

# Batas lapangan (sesuaikan dengan court.png)
LEFT, RIGHT = 120, 880
TOP, BOTTOM = 70, 660
BALL_R = 12

# Memuat gambar
def gambar(nama, ukuran):
    path = os.path.join(folder, nama)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, ukuran)

court = gambar("court.jpg", (W, H))
player = gambar("player.png", (90, 110))
opponent = gambar("opponent.png", (80, 100))
ball_img = gambar("ball.png", (25, 25))

# Posisi karakter dan bola
px, py = W // 2, 550
ox, oy = W // 2, 130
bx, by = W // 2, 350

vx, vy = 3, 5
skor_kamu = 0
skor_lawan = 0

pukul = 0
prev = None
smooth = None

# Webcam
cam = cv2.VideoCapture(0)

# Font skor
score_font = pygame.font.SysFont("georgia", 32, bold=True)
label_font = pygame.font.SysFont("arial", 14, bold=True)

jalan = True

while jalan:
    clock.tick(60)

    # Menutup game lewat tombol X jendela
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            jalan = False

    # Deteksi sarung tangan biru
    ok, frame = cam.read()
    terdeteksi = False

    if ok:
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(
            hsv,
            np.array([100, 90, 50]),
            np.array([135, 255, 255])
        )

        kontur, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if kontur:
            terbesar = max(kontur, key=cv2.contourArea)

            if cv2.contourArea(terbesar) > 500:
                x, y, w, h = cv2.boundingRect(terbesar)

                tx = 100 + (x + w / 2) / frame.shape[1] * (W - 200)
                ty = 400 + (y + h / 2) / frame.shape[0] * 220

                if smooth is None:
                    smooth = [tx, ty]

                smooth[0] += (tx - smooth[0]) * 0.4
                smooth[1] += (ty - smooth[1]) * 0.4

                px, py = smooth
                terdeteksi = True

                tangan = (x + w // 2, y + h // 2)

                # Gerakan cepat tangan memicu pukulan
                if prev is not None:
                    dx = tangan[0] - prev[0]
                    dy = tangan[1] - prev[1]

                    if (dx * dx + dy * dy) ** 0.5 > 35:
                        pukul = 12

                prev = tangan
            else:
                prev = None
        else:
            prev = None

        cv2.imshow("Deteksi Sarung Tangan", frame)

    # Batas gerak pemain
    px = max(100, min(W - 100, px))
    py = max(400, min(H - 85, py))

    # Gerakan bola
    bx += vx
    by += vy

    # Pantulan di sisi lapangan
    if bx - BALL_R <= LEFT:
        bx = LEFT + BALL_R
        vx = abs(vx)

    elif bx + BALL_R >= RIGHT:
        bx = RIGHT - BALL_R
        vx = -abs(vx)

    # Komputer mengikuti prediksi bola
    if vy < 0:
        target_x = bx + vx * 8
    else:
        target_x = bx

    ox += max(-5, min(5, target_x - ox))
    oy += max(-3, min(3, 100 - oy))
    ox = max(100, min(W - 100, ox))

    # Ukuran area tabrakan karakter
    PLAYER_RX, PLAYER_RY = 45, 55
    BOT_RX, BOT_RY = 43, 50

    # Pukulan pemain
    if pukul > 0:
        pukul -= 1

    kena_pemain = (
        abs(bx - px) < PLAYER_RX + BALL_R
        and abs(by - py) < PLAYER_RY + BALL_R
    )

    if kena_pemain and vy > 0 and pukul > 0:
        by = py - PLAYER_RY - BALL_R
        vy = -abs(vy) - 1
        vx = max(-6, min(6, (bx - px) * 0.15))
        pukul = 0

    # Pukulan komputer
    kena_bot = (
        abs(bx - ox) < BOT_RX + BALL_R
        and abs(by - oy) < BOT_RY + BALL_R
    )

    if kena_bot and vy < 0:
        by = oy + BOT_RY + BALL_R
        vy = abs(vy) + 1
        vx = max(-5, min(5, (px - bx) * 0.015))

    # Skor saat bola keluar dari batas lapangan
    if by + BALL_R >= BOTTOM:
        skor_lawan += 1
        bx, by = (LEFT + RIGHT) // 2, 350
        vx, vy = 3, 5
        pukul = 0

    elif by - BALL_R <= TOP:
        skor_kamu += 1
        bx, by = (LEFT + RIGHT) // 2, 350
        vx, vy = -3, -5
        pukul = 0

    # Gambar lapangan dan karakter
    screen.blit(court, (0, 0))

    screen.blit(
        opponent,
        opponent.get_rect(center=(int(ox), int(oy)))
    )

    screen.blit(
        player,
        player.get_rect(center=(int(px), int(py)))
    )

    screen.blit(
        ball_img,
        ball_img.get_rect(center=(int(bx), int(by)))
    )

    # Panel skor
    panel = pygame.Surface((280, 76), pygame.SRCALPHA)

    pygame.draw.rect(
        panel,
        (30, 20, 35, 210),
        (0, 0, 280, 76),
        border_radius=18
    )

    screen.blit(panel, (W // 2 - 140, 18))

    # Label skor
    you = label_font.render("YOU", True, (255, 190, 210))
    cpu = label_font.render("BOT", True, (255, 190, 210))

    screen.blit(you, (W // 2 - 105, 29))
    screen.blit(cpu, (W // 2 + 55, 29))

    # Angka skor
    score_you = score_font.render(
        str(skor_kamu), True, (255, 255, 255)
    )
    score_cpu = score_font.render(
        str(skor_lawan), True, (255, 255, 255)
    )
    separator = score_font.render(
        ":", True, (255, 150, 190)
    )

    screen.blit(
        score_you,
        score_you.get_rect(center=(W // 2 - 65, 62))
    )
    screen.blit(
        separator,
        separator.get_rect(center=(W // 2, 57))
    )
    screen.blit(
        score_cpu,
        score_cpu.get_rect(center=(W // 2 + 65, 62))
    )

    pygame.display.flip()

# Tutup webcam dan game
cam.release()
cv2.destroyAllWindows()
pygame.quit()
