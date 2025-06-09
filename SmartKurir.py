import pygame
import sys
import os
import random
import numpy as np
import heapq
from tkinter import Tk, filedialog

pygame.init()

# --- KONFIGURASI AWAL ---
WIDTH, HEIGHT = 1000, 700  # Ukuran jendela default
GRID_SIZE = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (120, 120, 120)
BIRU_M = (75, 200, 226)

# --- STATUS GAME ---
MAP_LOADED = False
MAP_SURFACE = None
MAP_ARRAY = None
COURIER_POS = (0, 0)
SOURCE_POS = (0, 0)
DEST_POS = (0, 0)
INITIAL_COURIER_POS = (0, 0)
COURIER_DIRECTION = 0
HAS_PACKAGE = False
PATH = []
CURRENT_PATH_INDEX = 0
MOVEMENT_SPEED = 5
RUNNING = False
FINISHED = False

# --- GAMBAR KURIR (Bentuk lebih runcing) ---
COURIER_IMGS = []
size = 30  # Ukuran surface
center = size // 2
for i in range(4):  # 0: Right, 1: Down, 2: Left, 3: Up
    img = pygame.Surface((size, size), pygame.SRCALPHA)
    if i == 0:  # Right
        # Ujung runcing di kanan
        points = [(5, 5), (size - 5, center), (5, size - 5)]
    elif i == 1:  # Down
        # Ujung runcing di bawah
        points = [(5, 5), (size - 5, 5), (center, size - 5)]
    elif i == 2:  # Left
        # Ujung runcing di kiri
        points = [(size - 5, 5), (5, center), (size - 5, size - 5)]
    elif i == 3:  # Up
        # Ujung runcing di atas
        points = [(5, size - 5), (size - 5, size - 5), (center, 5)]
    pygame.draw.polygon(img, BLACK, points)
    COURIER_IMGS.append(img)


# --- GAMBAR BENDERA ---
FLAG_SIZE = (20, 20)
YELLOW_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(YELLOW_FLAG, YELLOW, (0, 0, 5, 20))
pygame.draw.polygon(YELLOW_FLAG, YELLOW, [(5, 0), (20, 5), (5, 10)])

RED_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(RED_FLAG, RED, (0, 0, 5, 20))
pygame.draw.polygon(RED_FLAG, RED, [(5, 0), (20, 5), (5, 10)])


# --- Inisialisasi Layar & UI ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Smart Kurir")
font = pygame.font.SysFont('Arial', 24)

button_width, button_height = 180, 40
button_spacing = 20
button_y = 20

load_map_button_rect = pygame.Rect(20, button_y, button_width, button_height)
randomize_button_rect = pygame.Rect(load_map_button_rect.right + button_spacing, button_y, button_width, button_height)
start_button_rect = pygame.Rect(randomize_button_rect.right + button_spacing, button_y, button_width, button_height)
reset_button_rect = pygame.Rect(start_button_rect.right + button_spacing, button_y, button_width, button_height)


def load_map():
    """Muat gambar map dan identifikasi warna jalan."""
    global MAP_LOADED, MAP_SURFACE, MAP_ARRAY, WIDTH, HEIGHT, screen

    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Pilih gambar map",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    if not file_path:
        return

    try:
        map_img = pygame.image.load(file_path)
        map_width, map_height = map_img.get_size()

        WIDTH, HEIGHT = map_width, map_height + 80
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        MAP_SURFACE = map_img

        map_array_rgb = pygame.surfarray.array3d(map_img)
        road_array_awal = np.zeros((map_height, map_width), dtype=bool)

        for y in range(map_height):
            for x in range(map_width):
                r, g, b = map_array_rgb[x][y]
                if (90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150 and
                        abs(r - g) <= 20 and abs(r - b) <= 20 and abs(g - b) <= 20):
                    road_array_awal[y][x] = True

        working_eroded_array = np.copy(road_array_awal)
        jumlah_lapisan_erosi = 1

        for _ in range(jumlah_lapisan_erosi):
            peta_acuan = np.copy(working_eroded_array)
            for r in range(map_height):
                for c in range(map_width):
                    if not peta_acuan[r][c]:
                        continue
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < map_height and 0 <= nc < map_width) or not peta_acuan[nr][nc]:
                            working_eroded_array[r][c] = False
                            break
        
        MAP_ARRAY = working_eroded_array
        MAP_LOADED = True
        randomize_positions()
        
        print(f"Map dimuat: {file_path}")

    except Exception as e:
        print(f"Gagal memuat map: {e}")

def randomize_positions():
    """Acak posisi kurir, sumber, dan tujuan di jalan yang valid."""
    global COURIER_POS, SOURCE_POS, DEST_POS, INITIAL_COURIER_POS
    
    if not MAP_LOADED:
        return

    road_positions = np.argwhere(MAP_ARRAY)
    if len(road_positions) < 3:
        print("Jalan tidak ditemukan di map.")
        return

    selected_indices = np.random.choice(len(road_positions), 3, replace=False)
    pos1, pos2, pos3 = road_positions[selected_indices]

    COURIER_POS = (pos1[1], pos1[0])
    INITIAL_COURIER_POS = COURIER_POS 
    SOURCE_POS = (pos2[1], pos2[0])
    DEST_POS = (pos3[1], pos3[0])
    
    reset_simulation()


def reset_simulation():
    """Reset simulasi ke kondisi awal."""
    global COURIER_POS, HAS_PACKAGE, PATH, CURRENT_PATH_INDEX, RUNNING, FINISHED
    COURIER_POS = INITIAL_COURIER_POS
    HAS_PACKAGE = False
    PATH = []
    CURRENT_PATH_INDEX = 0
    RUNNING = False
    FINISHED = False

def start_simulation():
    """Mulai atau jeda simulasi."""
    global RUNNING
    if not MAP_LOADED or FINISHED:
        return
    RUNNING = not RUNNING
    if RUNNING and not PATH:
        calculate_path()

def calculate_path():
    """Menghitung path A*."""
    global PATH, CURRENT_PATH_INDEX
    start_node = (int(COURIER_POS[0]), int(COURIER_POS[1]))
    target_node = SOURCE_POS if not HAS_PACKAGE else DEST_POS
    PATH = find_path(start_node, target_node)
    CURRENT_PATH_INDEX = 0
    if not PATH:
        print(f"Tidak ada path ditemukan.")
        global RUNNING
        RUNNING = False

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(start, end):
    if not MAP_LOADED or not MAP_ARRAY[end[1]][end[0]] or not MAP_ARRAY[start[1]][start[0]]:
        return []

    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    open_set_hash = {start}

    while open_set:
        _, current = heapq.heappop(open_set)
        open_set_hash.remove(current)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            nx, ny = neighbor

            if 0 <= nx < MAP_ARRAY.shape[1] and 0 <= ny < MAP_ARRAY.shape[0] and MAP_ARRAY[ny][nx]:
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
    return []

def update_courier():
    """Update posisi kurir dengan logika belok yang sangat mulus."""
    global COURIER_POS, COURIER_DIRECTION, HAS_PACKAGE, PATH, CURRENT_PATH_INDEX, RUNNING, FINISHED
    
    if not RUNNING or not PATH or CURRENT_PATH_INDEX >= len(PATH):
        return

    if COURIER_POS == PATH[CURRENT_PATH_INDEX]:
        CURRENT_PATH_INDEX += 1
        
        if CURRENT_PATH_INDEX >= len(PATH):
            # Cek apakah misi selesai
            if not HAS_PACKAGE and COURIER_POS == SOURCE_POS:
                HAS_PACKAGE = True
                calculate_path()
            elif HAS_PACKAGE and COURIER_POS == DEST_POS:
                RUNNING = False
                FINISHED = True
                print("Paket berhasil diantar!")

    # Dapatkan titik target berikutnya dari path
    target_pos = PATH[CURRENT_PATH_INDEX]
    
    # Hitung vektor (dx, dy) ke target
    dx = target_pos[0] - COURIER_POS[0]
    dy = target_pos[1] - COURIER_POS[1]

    # Tentukan arah yang seharusnya (required direction)
    required_direction = COURIER_DIRECTION
    if dx > 0: required_direction = 0  # Kanan
    elif dx < 0: required_direction = 2  # Kiri
    elif dy > 0: required_direction = 1  # Bawah
    elif dy < 0: required_direction = 3  # Atas
    
    # Jika arah saat ini belum benar, berbelok di tempat dan jangan bergerak
    if COURIER_DIRECTION != required_direction:
        COURIER_DIRECTION = required_direction
        return # Jeda satu frame untuk animasi belok

    # Jika arah sudah benar, bergerak maju
    move_x = min(MOVEMENT_SPEED, abs(dx)) * (1 if dx > 0 else -1 if dx < 0 else 0)
    move_y = min(MOVEMENT_SPEED, abs(dy)) * (1 if dy > 0 else -1 if dy < 0 else 0)
    
    COURIER_POS = (COURIER_POS[0] + move_x, COURIER_POS[1] + move_y)


def draw_ui():
    """Menggambar elemen UI."""
    pygame.draw.rect(screen, BLACK, load_map_button_rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, randomize_button_rect, border_radius=5)
    pygame.draw.rect(screen, RED if RUNNING else BLACK, start_button_rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, reset_button_rect, border_radius=5)
    
    font_color = WHITE
    load_text = font.render("Load Map", True, font_color)
    random_text = font.render("Randomize", True, font_color)
    start_text = font.render("Start" if not RUNNING else "Pause", True, font_color)
    reset_text = font.render("Reset", True, font_color)

    screen.blit(load_text, load_text.get_rect(center=load_map_button_rect.center))
    screen.blit(random_text, random_text.get_rect(center=randomize_button_rect.center))
    screen.blit(start_text, start_text.get_rect(center=start_button_rect.center))
    screen.blit(reset_text, reset_text.get_rect(center=reset_button_rect.center))

    status_text = "Map belum dimuat"
    if MAP_LOADED:
        if FINISHED: status_text = "Pengantaran selesai!"
        elif RUNNING: status_text = "Mengantar paket..." if HAS_PACKAGE else "Menuju titik jemput..."
        else: status_text = "Siap untuk memulai"
    
    status_render = font.render(status_text, True, BLACK)
    screen.blit(status_render, (20, HEIGHT - 40))

def draw_game():
    """Menggambar elemen game."""
    if not MAP_LOADED:
        return
    
    map_y_offset = 80
    screen.blit(MAP_SURFACE, (0, map_y_offset))
    
    if not HAS_PACKAGE:
        screen.blit(YELLOW_FLAG, (SOURCE_POS[0] - 10, SOURCE_POS[1] - 10 + map_y_offset))
    screen.blit(RED_FLAG, (DEST_POS[0] - 10, DEST_POS[1] - 10 + map_y_offset))
    
    courier_img = COURIER_IMGS[COURIER_DIRECTION]
    courier_rect = courier_img.get_rect(center=(COURIER_POS[0], COURIER_POS[1] + map_y_offset))
    screen.blit(courier_img, courier_rect)

def main():
    """Loop utama game."""
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if load_map_button_rect.collidepoint(event.pos): load_map()
                elif randomize_button_rect.collidepoint(event.pos): randomize_positions()
                elif start_button_rect.collidepoint(event.pos): start_simulation()
                elif reset_button_rect.collidepoint(event.pos): reset_simulation()
        
        if RUNNING:
            update_courier()
        
        screen.fill(BIRU_M)
        draw_ui()
        draw_game()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
