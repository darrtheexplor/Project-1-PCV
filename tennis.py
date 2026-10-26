import pygame
import cv2
import numpy as np
import random
import sys

# 1. INISIALISASI GAME
pygame.init()

WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TENNIS - WEBCAM GLOVE GAME")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 28, bold=True)
small_font = pygame.font.SysFont("Arial", 17)
big_font = pygame.font.SysFont("Arial", 40, bold=True)

# Warna
BG = (20, 24, 38)
COURT = (35, 125, 85)
WHITE = (245, 245, 245)
RED = (255, 75, 85)
BLUE = (80, 155, 255)
YELLOW = (255, 235, 90)
GRAY = (155, 165, 180)
GREEN = (70, 255, 140)

# Batas lapangan
LEFT = 60
RIGHT = 940
TOP = 100
BOTTOM = 520
NET_X = WIDTH // 2

# 2. WEBCAM
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    pygame.quit()
    raise RuntimeError(
        "Webcam gagal dibuka. Tutup aplikasi kamera lain "
        "atau coba ganti VideoCapture(0) menjadi VideoCapture(1)."
    )

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Posisi tangan
hand_y = HEIGHT / 2
previous_hand_x = None
swing_timer = 0
hand_detected = False

# Sesuaikan jika sarung tangan tidak terdeteksi
SWING_THRESHOLD = 18
MIN_GLOVE_AREA = 500

# 3. PEMAIN DAN RAKET
paddle_w = 24
paddle_h = 100

player = pygame.Rect(
    110, HEIGHT // 2 - paddle_h // 2,
    paddle_w, paddle_h
)

opponent = pygame.Rect(
    866, HEIGHT // 2 - paddle_h // 2,
    paddle_w, paddle_h
)

AI_SPEED = 3.8

# 4. BOLA DAN SKOR
ball_radius = 12

ball_x = float(WIDTH // 2)
ball_y = float(HEIGHT // 2)

ball_vx = -5.0
ball_vy = random.choice([-3.0, 3.0])

player_score = 0
opponent_score = 0

message = "Show your RED glove to the webcam"


def reset_ball(direction):
    global ball_x, ball_y, ball_vx, ball_vy

    ball_x = WIDTH / 2
    ball_y = random.randint(TOP + 50, BOTTOM - 50)

    ball_vx = 5.0 * direction
    ball_vy = random.choice([-3.5, -2.5, 2.5, 3.5])


def draw_text(text, x, y, color=WHITE, selected_font=None):
    if selected_font is None:
        selected_font = small_font

    image = selected_font.render(text, True, color)
    screen.blit(image, (x, y))


def draw_racket(rect, color):
    # Raket dibuat seperti paddle arcade
    pygame.draw.rect(
        screen, color, rect, border_radius=10
    )

    # Garis kecil di tengah raket
    pygame.draw.line(
        screen, WHITE,
        (rect.centerx, rect.top + 15),
        (rect.centerx, rect.bottom - 15),
        2
    )


# 5. GAME LOOP
running = True

try:
    while running:
        clock.tick(60)

        # INPUT DAN EVENT
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Reset skor
                if event.key == pygame.K_r:
                    player_score = 0
                    opponent_score = 0
                    reset_ball(-1)

        keys = pygame.key.get_pressed()

        # BACA WEBCAM
        success, frame = cap.read()
        hand_detected = False
        swing_active = False

        if success:
            # Mirror seperti cermin
            frame = cv2.flip(frame, 1)

            hsv = cv2.cvtColor(
                frame, cv2.COLOR_BGR2HSV
            )

            # Deteksi warna merah pada HSV
            lower1 = np.array([0, 100, 80])
            upper1 = np.array([10, 255, 255])

            lower2 = np.array([170, 100, 80])
            upper2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)

            # Mengurangi noise
            kernel = np.ones((5, 5), np.uint8)

            mask = cv2.morphologyEx(
                mask, cv2.MORPH_OPEN, kernel
            )

            mask = cv2.dilate(
                mask, kernel, iterations=1
            )

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest = max(
                    contours, key=cv2.contourArea
                )

                area = cv2.contourArea(largest)

                if area > MIN_GLOVE_AREA:
                    moments = cv2.moments(largest)

                    if moments["m00"] != 0:
                        cx = int(
                            moments["m10"] / moments["m00"]
                        )
                        cy = int(
                            moments["m01"] / moments["m00"]
                        )

                        hand_detected = True

                        # Tandai posisi sarung tangan
                        cv2.circle(
                            frame, (cx, cy),
                            12, (0, 255, 0), -1
                        )

                        # Gerakan horizontal cepat
                        if previous_hand_x is not None:
                            dx = cx - previous_hand_x

                            if abs(dx) > SWING_THRESHOLD:
                                swing_timer = 10

                        previous_hand_x = cx

                        # Posisi vertikal tangan
                        cam_h, cam_w = frame.shape[:2]

                        target_y = (
                            TOP + paddle_h / 2
                            + (cy / cam_h)
                            * (BOTTOM - TOP - paddle_h)
                        )

                        # Smooth movement
                        hand_y += (target_y - hand_y) * 0.4

                        player.centery = int(hand_y)

                        # Batasi raket di area kiri
                        player.clamp_ip(
                            pygame.Rect(
                                LEFT, TOP,
                                NET_X - LEFT - 20,
                                BOTTOM - TOP
                            )
                        )

            if swing_timer > 0:
                swing_timer -= 1
                swing_active = True

            # Tampilkan status deteksi
            status = (
                "GLOVE DETECTED"
                if hand_detected else "SEARCHING RED GLOVE"
            )

            cv2.putText(
                frame, status, (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0) if hand_detected
                else (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                "Move vertically | Swing horizontally",
                (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1
            )

            cv2.imshow("Webcam - Red Glove", frame)
            cv2.imshow("Color Detection", mask)

            # Q juga bisa menutup game
            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False

        # KONTROL CADANGAN KEYBOARD
        # W/S untuk menggerakkan raket
        # SPACE untuk melakukan pukulan manual
        if keys[pygame.K_w]:
            player.y -= 6

        if keys[pygame.K_s]:
            player.y += 6

        player.clamp_ip(
            pygame.Rect(
                LEFT, TOP,
                NET_X - LEFT - 20,
                BOTTOM - TOP
            )
        )

        if keys[pygame.K_SPACE]:
            swing_active = True

        # GERAKAN LAWAN KOMPUTER
        # AI mencoba mengikuti posisi bola
        if ball_vx > 0:
            target_ai_y = ball_y
        else:
            target_ai_y = HEIGHT / 2

        if opponent.centery < target_ai_y - 10:
            opponent.y += AI_SPEED
        elif opponent.centery > target_ai_y + 10:
            opponent.y -= AI_SPEED

        opponent.clamp_ip(
            pygame.Rect(
                NET_X + 20, TOP,
                RIGHT - NET_X - 20,
                BOTTOM - TOP
            )
        )

        # GERAKAN BOLA
        ball_x += ball_vx
        ball_y += ball_vy

        # Pantulan atas dan bawah
        if ball_y - ball_radius <= TOP:
            ball_y = TOP + ball_radius
            ball_vy = abs(ball_vy)

        elif ball_y + ball_radius >= BOTTOM:
            ball_y = BOTTOM - ball_radius
            ball_vy = -abs(ball_vy)

        ball_rect = pygame.Rect(
            int(ball_x - ball_radius),
            int(ball_y - ball_radius),
            ball_radius * 2,
            ball_radius * 2
        )

        # PUKULAN PEMAIN
        if (
            ball_rect.colliderect(player)
            and ball_vx < 0
        ):
            if swing_active:
                # Bola dipukul kembali ke arah lawan
                ball_x = player.right + ball_radius
                ball_vx = abs(ball_vx) + 0.3

                # Sudut bola berdasarkan posisi tabrakan
                offset = (
                    ball_y - player.centery
                ) / (paddle_h / 2)

                ball_vy = offset * 5.0

                message = "NICE SHOT!"

            else:
                # Bola menyentuh raket, tetapi belum dipukul
                pass

        # Jika bola melewati pemain kiri
        if ball_x < LEFT:
            opponent_score += 1
            message = "Opponent scores!"
            reset_ball(1)

        # PUKULAN LAWAN KOMPUTER
        if (
            ball_rect.colliderect(opponent)
            and ball_vx > 0
        ):
            ball_x = opponent.left - ball_radius
            ball_vx = -abs(ball_vx)

            offset = (
                ball_y - opponent.centery
            ) / (paddle_h / 2)

            ball_vy = offset * 4.5

        # Jika bola melewati lawan
        if ball_x > RIGHT:
            player_score += 1
            message = "YOU SCORE!"
            reset_ball(-1)

        # GAMBAR ARENA
        screen.fill(BG)

        pygame.draw.rect(
            screen, COURT,
            (LEFT, TOP, RIGHT - LEFT, BOTTOM - TOP)
        )

        # Garis batas lapangan
        pygame.draw.rect(
            screen, WHITE,
            (LEFT + 30, TOP + 25,
             RIGHT - LEFT - 60,
             BOTTOM - TOP - 50),
            2
        )

        # Garis net putus-putus
        for y in range(TOP, BOTTOM, 22):
            pygame.draw.line(
                screen, WHITE,
                (NET_X, y), (NET_X, y + 12), 3
            )

        # Raket pemain dan lawan
        draw_racket(player, RED)
        draw_racket(opponent, BLUE)

        # Bola
        pygame.draw.circle(
            screen, YELLOW,
            (int(ball_x), int(ball_y)),
            ball_radius
        )

        # Efek garis bola saat bergerak
        pygame.draw.line(
            screen, YELLOW,
            (int(ball_x - ball_vx * 2),
             int(ball_y - ball_vy * 2)),
            (int(ball_x), int(ball_y)),
            3
        )

        # Skor
        draw_text(
            str(player_score), 400, 35,
            RED, big_font
        )

        draw_text(
            str(opponent_score), 560, 35,
            BLUE, big_font
        )

        draw_text(
            "YOU", 100, 65, RED, small_font
        )

        draw_text(
            "COMPUTER", 820, 65, BLUE, small_font
        )

        # Status kontrol
        control_status = (
            "WEBCAM ACTIVE"
            if hand_detected else "SHOW RED GLOVE"
        )

        draw_text(
            control_status, 65, 545,
            GREEN if hand_detected else GRAY,
            small_font
        )

        draw_text(
            "Move hand up/down | Swing sideways to hit",
            320, 545, WHITE, small_font
        )

        draw_text(
            "SPACE: hit | W/S: move | R: reset | ESC: quit",
            255, 570, GRAY, small_font
        )

        pygame.display.flip()

finally:
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()
