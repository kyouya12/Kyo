import pygame
import sys
import os
import random
import numpy as np
import heapq
from tkinter import Tk, filedialog

pygame.init()

WIDTH, HEIGHT = 1000, 700 #ukuran windows lebar x tinggi
GRID_SIZE = 10  # ukuran petak dilayar
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (120, 120, 120)  # warna jalan
BIRU_M = (75, 200, 226)

# status game
MAP_LOADED = False
MAP_SURFACE = None
MAP_ARRAY = None
COURIER_POS = (0, 0)
SOURCE_POS = (0, 0)
DEST_POS = (0, 0)
COURIER_DIRECTION = 0  # 0: right, 1: down-right, 2: down, 3: down-left, 4: left, 5: up-left, 6: up, 7: up-right
HAS_PACKAGE = False
PATH = []
CURRENT_PATH_INDEX = 0
MOVEMENT_SPEED = 5  # jalan per pixel
RUNNING = False
FINISHED = False

# gambar kurir (Bentuk segitiga sama kaki)
COURIER_IMGS = []
for i in range(8):  # 0: right, 1: down, 2: left, 3: up
    img = pygame.Surface((60, 20), pygame.SRCALPHA) 
    
    base_height_for_lr = 18 
    base_width_for_ud = 18  
    length_lr = 25          
    length_ud = 18          

    y_mid = 20 // 2 
    
    y_top_base_lr = (20 - base_height_for_lr) // 2      
    y_bottom_base_lr = y_top_base_lr + base_height_for_lr 

    x_left_base_ud = 0 
    x_right_base_ud = x_left_base_ud + base_width_for_ud

    if i == 0:  # Right (Kanan)
        pygame.draw.polygon(img, BLACK, [
            (0, y_top_base_lr),             
            (length_lr, y_mid),             
            (0, y_bottom_base_lr)           
        ])
    elif i == 1:  # Down (Bawah)
        tip_x = (x_left_base_ud + x_right_base_ud) // 2
        pygame.draw.polygon(img, BLACK, [
            (x_left_base_ud, 0),            
            (x_right_base_ud, 0),           
            (tip_x, length_ud)              
        ])
    elif i == 2:  # Left (Kiri)
        pygame.draw.polygon(img, BLACK, [
            (length_lr, y_top_base_lr),     
            (0, y_mid),                     
            (length_lr, y_bottom_base_lr)   
        ])
    elif i == 3:  # Up (Atas)
        base_y = 19 
        tip_x = (x_left_base_ud + x_right_base_ud) // 2
        tip_y = base_y - length_ud
        pygame.draw.polygon(img, BLACK, [
            (x_left_base_ud, base_y),       
            (x_right_base_ud, base_y),      
            (tip_x, tip_y)                  
        ])

    COURIER_IMGS.append(img)

# Gambar Bentuk bendera
FLAG_SIZE = (20, 20) #ukuran bendera
YELLOW_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(YELLOW_FLAG, YELLOW, (0, 0, 5, 20)) #bentuk persegi kiri
pygame.draw.polygon(YELLOW_FLAG, YELLOW, [(5, 0), (20, 5), (5, 10)]) #bentuk segitiga kanan

RED_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(RED_FLAG, RED, (0, 0, 5, 20))
pygame.draw.polygon(RED_FLAG, RED, [(5, 0), (20, 5), (5, 10)])

# inisialisasi pada layar
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game smart kurir")

# font tampilan layar
font = pygame.font.SysFont('Arial', 24)

# element tampilan
button_width, button_height = 180, 40 #lebar tombol dan tinggi
button_spacing = 60 #jarak antar tombol pada layar
button_y = 10 # jarak 10 piksel dari atas layar.

# posisi tombol
load_map_button_rect = pygame.Rect(20, button_y, button_width, button_height)
randomize_button_rect = pygame.Rect(20 + button_width + button_spacing, button_y, button_width, button_height)
start_button_rect = pygame.Rect(20 + (button_width + button_spacing) * 2, button_y, button_width, button_height)
reset_button_rect = pygame.Rect(20 + (button_width + button_spacing) * 3, button_y, button_width, button_height)

def load_map():
    """Muat gambar map dan identifikasi warna jalan"""
    global MAP_LOADED, MAP_SURFACE, MAP_ARRAY, WIDTH, HEIGHT, screen
    
    root = Tk()
    root.withdraw()  #sembunyikan root window
    
    file_path = filedialog.askopenfilename(
        title="Pilih gambar map",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    
    # jika tidak memilih map maka kembali ke layar
    if not file_path:
        return
    
   # memuat gambar map
    try:
        map_img = pygame.image.load(file_path)
        # map_width dan map_height adalah dimensi gambar peta dalam piksel
        map_width, map_height = map_img.get_size()
        
        # memeriksa ukuran gambar
        if not (1000 <= map_width <= 1500 and 700 <= map_height <= 1000):
            print(f"Map size {map_width}x{map_height} outside allowed range")
            return
        
        # menambah ukuran layar supaya menyesuaikan dengan map
        WIDTH, HEIGHT = map_width, map_height + 80  # ukuran tambahan untuk tampilan ui
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        # Menyimpan map ke dalam map_surface
        MAP_SURFACE = map_img
        
        # mengubah gambar jadi array rgb supaya bisa diproses
        # map_array_rgb (sebelumnya map_array di kode Anda) akan berdimensi (map_width, map_height, 3)
        map_array_rgb = pygame.surfarray.array3d(map_img)
        # road_array (peta jalan boolean awal) akan berdimensi (map_height, map_width)
        road_array_awal = np.zeros((map_height, map_width), dtype=bool)
        
        # identifikasi warna jalan
        for y_coord in range(map_height):
            for x_coord in range(map_width):
                # Ambil RGB dari map_array_rgb[x_coord][y_coord]
                r, g, b = map_array_rgb[x_coord][y_coord]
                # cek warna jalan (hanya abu-abu sesuai kode Anda)
                if ((90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150 and
                     abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15) #gray
                ):
                    # Simpan ke road_array_awal[y_coord][x_coord]
                    road_array_awal[y_coord][x_coord] = True
        
        # --- MULAI PROSES EROSI PETA JALAN (MULTI-LAPIS) ---
        # road_array_awal adalah peta jalan sebelum erosi.
        
        working_eroded_array = np.copy(road_array_awal) # Mulai dengan salinan peta asli
        
        # Tentukan jumlah lapisan erosi yang diinginkan
        # Idealnya sekitar setengah dari "ketebalan" visual kurir Anda.
        # Jika kurir secara visual "tebal" sekitar 18 piksel, coba 9 atau 10.
        # Mulai dengan angka yang lebih kecil dulu (misalnya 3 atau 5) untuk melihat efeknya.
        jumlah_lapisan_erosi = 5 # Anda bisa sesuaikan angka ini

        for i_pass in range(jumlah_lapisan_erosi):
            peta_acuan_untuk_lapisan_ini = np.copy(working_eroded_array)
            peta_hasil_lapisan_ini = np.copy(working_eroded_array) # Tempat menyimpan hasil erosi lapisan ini

            for r_idx in range(map_height): 
                for c_idx in range(map_width):  
                    
                    if not peta_acuan_untuk_lapisan_ini[r_idx][c_idx]:
                        continue

                    is_pixel_on_edge_in_this_pass = False
                    neighbor_pixel_coordinates = [
                        (r_idx - 1, c_idx), (r_idx + 1, c_idx),
                        (r_idx, c_idx - 1), (r_idx, c_idx + 1)
                    ]
                    for nr, nc in neighbor_pixel_coordinates:
                        if not (0 <= nr < map_height and 0 <= nc < map_width): 
                            is_pixel_on_edge_in_this_pass = True 
                            break
                        if not peta_acuan_untuk_lapisan_ini[nr][nc]: 
                            is_pixel_on_edge_in_this_pass = True
                            break
                    
                    if is_pixel_on_edge_in_this_pass:
                        peta_hasil_lapisan_ini[r_idx][c_idx] = False 
            
            working_eroded_array = peta_hasil_lapisan_ini 

        # MAP_ARRAY global akan menggunakan peta yang sudah dierosi berkali-kali
        MAP_ARRAY = working_eroded_array 
        # --- AKHIR PROSES EROSI PETA JALAN ---
        
        MAP_LOADED = True
        
        # Reset positions and path (akan menggunakan MAP_ARRAY yang sudah dierosi)
        randomize_positions()
        reset_simulation()
        
        print(f"Map loaded: {file_path}")
        print(f"Map size: {map_width}x{map_height}")
        # Menampilkan jumlah piksel jalan sebelum dan sesudah erosi
        print(f"Roads identified (original): {np.sum(road_array_awal)} pixels")
        print(f"Roads identified (eroded for pathfinding): {np.sum(MAP_ARRAY)} pixels")
        
    except Exception as e:
        print(f"Error loading map: {e}")

def randomize_positions():
    """Randomize courier, source, and destination positions on valid road tiles"""
    global COURIER_POS, SOURCE_POS, DEST_POS, COURIER_DIRECTION, HAS_PACKAGE, PATH
    
    if not MAP_LOADED:
        return
    
    # Get all road positions
    road_positions = np.argwhere(MAP_ARRAY)
    
    if len(road_positions) < 3:
        print("Not enough road positions found")+_
        return
    
    # Shuffle positions
    np.random.shuffle(road_positions)
    
    # Select positions for courier, source, and destination
    y, x = road_positions[0]
    COURIER_POS = (x, y)
    
    y, x = road_positions[1]
    SOURCE_POS = (x, y)
    
    y, x = road_positions[2]
    DEST_POS = (x, y)
    
    # Random courier direction
    COURIER_DIRECTION = random.randint(0, 3)
    
    # Reset package and path
    HAS_PACKAGE = False
    PATH = []
    CURRENT_PATH_INDEX = 0
    FINISHED = False

def reset_simulation():
    """Reset the simulation state without changing positions"""
    global HAS_PACKAGE, PATH, CURRENT_PATH_INDEX, RUNNING, FINISHED
    
    HAS_PACKAGE = False
    PATH = []
    CURRENT_PATH_INDEX = 0
    RUNNING = False
    FINISHED = False

def start_simulation():
    """Start the courier pathfinding and movement"""
    global RUNNING, PATH, CURRENT_PATH_INDEX
    
    if not MAP_LOADED or FINISHED:
        return
    
    RUNNING = not RUNNING
    
    if RUNNING and not PATH:
        # If no path is calculated, calculate it now
        calculate_path()

def calculate_path():
    """Calculate the path from courier to source and then to destination"""
    global PATH, CURRENT_PATH_INDEX, HAS_PACKAGE
    
    if not HAS_PACKAGE:
        # First path: courier to source
        target = SOURCE_POS
    else:
        # Second path: source to destination
        target = DEST_POS
    
    PATH = find_path(COURIER_POS, target)
    CURRENT_PATH_INDEX = 0
    
    if not PATH:
        print(f"No path found to {'source' if not HAS_PACKAGE else 'destination'}")
        RUNNING = False

def find_path(start, end):
    """A* pathfinding algorithm to find a path from start to end"""
    if not MAP_LOADED or not MAP_ARRAY[end[1]][end[0]] or not MAP_ARRAY[start[1]][start[0]]:
        return []
    
    # A* algorithm
    open_set = [(0, start)]  # Priority queue: (f_score, position)
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    
    # For open_set lookup
    open_set_hash = {start}
    
    while open_set:
        current_f, current = heapq.heappop(open_set)
        open_set_hash.remove(current)
        
        if current == end:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(current)  # Add start position
            path.reverse()
            return path
        
        # Check all neighbors (4-way movement)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = current[0] + dx, current[1] + dy
            
            # Check if within bounds and is road
            if (0 <= x < MAP_ARRAY.shape[1] and 0 <= y < MAP_ARRAY.shape[0] and 
                MAP_ARRAY[y][x]):
                
                neighbor = (x, y)
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # This path is better
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
    
    # No path found
    return []

def heuristic(a, b):
    """Manhattan distance heuristic"""
    return abs(a[0] - b[0]) + abs(a[1] - b[0])

def update_courier():
    """Update courier position along the path"""
    global COURIER_POS, COURIER_DIRECTION, HAS_PACKAGE, PATH, CURRENT_PATH_INDEX, RUNNING, FINISHED
    
    if not RUNNING or not PATH or CURRENT_PATH_INDEX >= len(PATH):
        return
    
    # Target position from path
    target_pos = PATH[CURRENT_PATH_INDEX]
    
    # Determine direction to target
    dx = target_pos[0] - COURIER_POS[0]
    dy = target_pos[1] - COURIER_POS[1]
    
    # Update courier direction based on movement
    if dx > 0:
        new_direction = 0  # Right
    elif dx < 0:
        new_direction = 2  # Left
    elif dy > 0:
        new_direction = 1  # Down
    elif dy < 0:
        new_direction = 3  # Up
    else:
        new_direction = COURIER_DIRECTION  # No change if at target
    
    # Smooth rotation to new direction
    if new_direction != COURIER_DIRECTION:
        COURIER_DIRECTION = new_direction
    
    # Move towards target position
    cx, cy = COURIER_POS
    tx, ty = target_pos
    
    # Calculate move vector
    move_x = min(MOVEMENT_SPEED, abs(tx - cx)) * (1 if tx > cx else -1 if tx < cx else 0)
    move_y = min(MOVEMENT_SPEED, abs(ty - cy)) * (1 if ty > cy else -1 if ty < cy else 0)
    
    # Update position
    new_x = cx + move_x
    new_y = cy + move_y
    COURIER_POS = (new_x, new_y)
    
    # Check if reached target position
    if abs(new_x - tx) < MOVEMENT_SPEED and abs(new_y - ty) < MOVEMENT_SPEED:
        COURIER_POS = target_pos  # Snap to grid
        CURRENT_PATH_INDEX += 1
        
        # Check if reached final destination
        if CURRENT_PATH_INDEX >= len(PATH):
            # If at source and don't have package, pick it up
            if not HAS_PACKAGE and COURIER_POS == SOURCE_POS:
                HAS_PACKAGE = True
                # Calculate new path to destination
                PATH = find_path(SOURCE_POS, DEST_POS)
                CURRENT_PATH_INDEX = 0
            # If at destination and have package, delivery complete
            elif HAS_PACKAGE and COURIER_POS == DEST_POS:
                RUNNING = False
                FINISHED = True
                print("Delivery complete!")

def draw_ui():
    """Menggambar element tampilan"""
    # Gambar tombol
    pygame.draw.rect(screen, BLACK, load_map_button_rect)
    pygame.draw.rect(screen, BLACK, randomize_button_rect)
    pygame.draw.rect(screen, BLACK if not RUNNING else RED, start_button_rect)
    pygame.draw.rect(screen, BLACK, reset_button_rect)
    
    # gambar teks tombol
    load_text = font.render("Load Map", True, WHITE)
    random_text = font.render("Randomize", True, WHITE)
    start_text = font.render("Start" if not RUNNING else "Pause", True, WHITE)
    reset_text = font.render("Reset", True, WHITE)
    
    #posisi teks dilayar
    screen.blit(load_text, (load_map_button_rect.x + 40, load_map_button_rect.y + 5))
    screen.blit(random_text, (randomize_button_rect.x + 45, randomize_button_rect.y + 5))
    screen.blit(start_text, (start_button_rect.x + 65, start_button_rect.y + 5))
    screen.blit(reset_text, (reset_button_rect.x + 65, reset_button_rect.y + 5))
    
    # Draw status text
    status_text = "Map not loaded"
    if MAP_LOADED:
        if FINISHED:
            status_text = "Delivery completed!"
        elif RUNNING:
            status_text = "Delivering..." if HAS_PACKAGE else "Going to pickup point..."
        else:
            status_text = "Ready to start"
    
    status_render = font.render(status_text, True, BLACK)
    screen.blit(status_render, (20, HEIGHT - 40))

def draw_game():
    """Draw game elements"""
    if not MAP_LOADED:
        return
    
    # Draw map
    screen.blit(MAP_SURFACE, (0, 80))
    
    # Draw source and destination
    screen.blit(YELLOW_FLAG, (SOURCE_POS[0] - 10, SOURCE_POS[1] - 10 + 80))
    screen.blit(RED_FLAG, (DEST_POS[0] - 10, DEST_POS[1] - 10 + 80))
    
    # Draw courier
    courier_img = COURIER_IMGS[COURIER_DIRECTION]
    screen.blit(courier_img, (COURIER_POS[0] - 10, COURIER_POS[1] - 10 + 80))
    

def main():
    """Main game loop"""
    global RUNNING
    
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if load_map_button_rect.collidepoint(event.pos):
                    load_map()
                elif randomize_button_rect.collidepoint(event.pos):
                    randomize_positions()
                elif start_button_rect.collidepoint(event.pos):
                    start_simulation()
                elif reset_button_rect.collidepoint(event.pos):
                    reset_simulation()
        
        # Update game state
        if RUNNING:
            update_courier()
        
        # Draw everything
        screen.fill(BIRU_M)
        draw_ui()
        draw_game()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
