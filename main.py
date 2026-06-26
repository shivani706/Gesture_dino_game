import pygame
import random
import cv2
from collections import deque, Counter
from gesture_detector import get_gesture, release as release_camera

# ---------- CONFIG ----------
WIDTH, HEIGHT = 900, 500
FPS = 60
GROUND_Y = 380
GRAVITY = 0.8

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (200, 30, 30)

# ---------- GESTURE SMOOTHER ----------
class GestureSmoother:
    def __init__(self, window=7):
        self.window = deque(maxlen=window)

    def update(self, raw):
        self.window.append(raw)
        return Counter(self.window).most_common(1)[0][0]

# ---------- CV2 -> PYGAME ----------
def cv2_to_pygame(frame_bgr):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    rgb = rgb.swapaxes(0, 1)
    return pygame.surfarray.make_surface(rgb)

# ---------- CAMERA HUD (rounded + label + glass) ----------
def draw_camera_hud(screen, cam_surface, x, y, w, h, label="LIVE CAMERA"):
    # Glass background
    glass = pygame.Surface((w, h), pygame.SRCALPHA)
    glass.fill((255, 255, 255, 80))
    screen.blit(glass, (x, y))

    # Rounded border
    pygame.draw.rect(screen, (0, 0, 0), (x, y, w, h), width=2, border_radius=14)

    # Label pill
    pill_w, pill_h = 135, 28
    pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
    pill.fill((0, 0, 0, 140))
    screen.blit(pill, (x + 10, y + 10))
    pygame.draw.rect(screen, (0, 0, 0), (x + 10, y + 10, pill_w, pill_h), width=1, border_radius=10)

    font = pygame.font.SysFont("Arial", 18, bold=True)
    txt = font.render(label, True, (255, 255, 255))
    screen.blit(txt, (x + 18, y + 14))

    # Inner camera area
    pad = 10
    inner_x = x + pad
    inner_y = y + 45
    inner_w = w - pad * 2
    inner_h = h - 55

    cam_scaled = pygame.transform.scale(cam_surface, (inner_w, inner_h))

    # Clip + draw (clean edges)
    prev_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(inner_x, inner_y, inner_w, inner_h))
    screen.blit(cam_scaled, (inner_x, inner_y))
    screen.set_clip(prev_clip)

    pygame.draw.rect(screen, (0, 0, 0), (inner_x, inner_y, inner_w, inner_h), width=1, border_radius=10)

# ---------- DINO ----------
class Dino:
    def __init__(self, image):
        self.image = image
        self.x = 80
        self.base_w = 60
        self.base_h = 60
        self.y = GROUND_Y - self.base_h
        self.vy = 0
        self.is_jumping = False
        self.is_ducking = False

    def jump(self):
        if not self.is_jumping:
            self.vy = -15
            self.is_jumping = True

    def duck(self, state):
        self.is_ducking = state

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy

        floor_y = GROUND_Y - self.base_h
        if self.y >= floor_y:
            self.y = floor_y
            self.vy = 0
            self.is_jumping = False

    def rect(self):
        h = 40 if self.is_ducking else self.base_h
        y = self.y + (self.base_h - h)
        return pygame.Rect(self.x, y, self.base_w, h)

    def draw(self, screen):
        h = 40 if self.is_ducking else self.base_h
        img = pygame.transform.scale(self.image, (self.base_w, h))
        screen.blit(img, (self.x, self.y + (self.base_h - h)))

# ---------- OBSTACLE ----------
class Obstacle:
    def __init__(self, image, speed):
        self.image = image
        self.w = 40
        self.h = 60
        self.x = WIDTH + 10
        self.y = GROUND_Y - self.h
        self.speed = speed

    def update(self):
        self.x -= self.speed

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def offscreen(self):
        return self.x < -60

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

# ---------- MAIN ----------
def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Gesture Dino")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 24)
    big = pygame.font.SysFont("Arial", 48)

    # Images
    dino_img = pygame.image.load("assets/dino.png").convert_alpha()
    cactus_img = pygame.image.load("assets/cactus.png").convert_alpha()
    cloud_img = pygame.image.load("assets/cloud.png").convert_alpha()

    dino_img = pygame.transform.scale(dino_img, (60, 60))
    cactus_img = pygame.transform.scale(cactus_img, (40, 60))
    cloud_img = pygame.transform.scale(cloud_img, (80, 40))

    # Sounds
    jump_sound = pygame.mixer.Sound("assets/jump.wav")
    hit_sound = pygame.mixer.Sound("assets/hit.wav")

    # Optional music (remove these 3 lines if you don’t have bg.mp3)
    pygame.mixer.music.load("assets/bg.mp3")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

    def reset():
        return {
            "dino": Dino(dino_img),
            "obs": [],
            "clouds": [],
            "score": 0,
            "speed": 7,
            "spawn_cd": 0,
            "jump_cd": 0,
            "game_over": False,
        }

    state = reset()
    smoother = GestureSmoother(window=7)
    prev_gesture = "NONE"

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and state["game_over"]:
                    pygame.mixer.music.play(-1)
                    state = reset()

        # ---- Gesture + Frame ----
        raw_gesture, cam_frame = get_gesture()
        gesture = smoother.update(raw_gesture)

        dino = state["dino"]

        # ---- Update ----
        if not state["game_over"]:
            if state["jump_cd"] > 0:
                state["jump_cd"] -= 1

            # Edge-trigger jump
            if gesture == "JUMP" and prev_gesture != "JUMP" and state["jump_cd"] == 0:
                dino.jump()
                jump_sound.play()
                state["jump_cd"] = 12

            dino.duck(gesture == "BEND")
            speed = state["speed"] + 2 if gesture == "RUN" else state["speed"]

            dino.update()

            # Spawn obstacles
            state["spawn_cd"] -= 1
            if state["spawn_cd"] <= 0:
                state["obs"].append(Obstacle(cactus_img, speed))
                state["spawn_cd"] = random.randint(55, 95)

            # Update obstacles
            for o in state["obs"]:
                o.speed = speed
                o.update()

            state["obs"] = [o for o in state["obs"] if not o.offscreen()]

            # Clouds
            if random.randint(1, 200) == 1:
                state["clouds"].append([WIDTH, random.randint(50, 150)])

            for cloud in state["clouds"]:
                cloud[0] -= 2

            state["clouds"] = [c for c in state["clouds"] if c[0] > -100]

            # Collision
            for o in state["obs"]:
                if dino.rect().colliderect(o.rect()):
                    hit_sound.play()
                    pygame.mixer.music.stop()
                    state["game_over"] = True
                    break

            # Score + difficulty
            state["score"] += 1
            if state["score"] % 500 == 0:
                state["speed"] += 1

        # ---- Draw ----
        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        # Clouds
        for cloud in state["clouds"]:
            screen.blit(cloud_img, (cloud[0], cloud[1]))

        # Dino + obstacles
        dino.draw(screen)
        for o in state["obs"]:
            o.draw(screen)

        # HUD
        hud = font.render(
            f"Raw: {raw_gesture}  Stable: {gesture}   Score: {state['score']//10}",
            True, BLACK
        )
        screen.blit(hud, (20, 20))

        # Camera HUD (top-right)
        if cam_frame is not None:
            cam_surface = cv2_to_pygame(cam_frame)
            cam_w, cam_h = 260, 200
            cam_x, cam_y = WIDTH - cam_w - 20, 20
            draw_camera_hud(screen, cam_surface, cam_x, cam_y, cam_w, cam_h, label="LIVE CAMERA")

        # Game over UI
        if state["game_over"]:
            over = big.render("GAME OVER", True, RED)
            tip = font.render("Press R to Restart", True, BLACK)
            screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2))

        pygame.display.flip()
        prev_gesture = gesture

    release_camera()
    pygame.quit()


if __name__ == "__main__":
    main()