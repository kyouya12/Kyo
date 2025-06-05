import pygame
import sys
import os
import random
import numpy as np
import heapq
from tkinter import Tk, filedialog

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700  # Default window size, will adjust based on loaded map
GRID_SIZE = 10  # Size of each grid cell
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (120, 120, 120)  # Road color

# Game state
MAP_LOADED = False
MAP_SURFACE = None
MAP_ARRAY = None
ROAD_CENTER_MAP = None  # Untuk menyimpan road center info
COURIER_POS = (0.0, 0.0)  # Float untuk gerakan halus
SOURCE_POS = (0, 0)
DEST_POS = (0, 0)
COURIER_DIRECTION = 0  # 0: right, 1: down, 2: left, 3: up
HAS_PACKAGE = False
PATH = []
CURRENT_PATH_INDEX = 0
MOVEMENT_SPEED = 2.5  # Speed untuk gerakan halus
RUNNING = False
FINISHED = False

# Courier images (triangle pointing in different directions)
COURIER_IMGS = []
for i in range(4):  # 0: right, 1: down, 2: left, 3: up
    img = pygame.Surface((20, 20), pygame.SRCALPHA)
    if i == 0:  # Right
        pygame.draw.polygon(img, RED, [(0, 0), (20, 10), (0, 20)])
    elif i == 1:  # Down
        pygame.draw.polygon(img, RED, [(0, 0), (20, 0), (10, 20)])
    elif i == 2:  # Left
        pygame.draw.polygon(img, RED, [(20, 0), (0, 10), (20, 20)])
    elif i == 3:  # Up
        pygame.draw.polygon(img, RED, [(0, 20), (10, 0), (20, 20)])
    COURIER_IMGS.append(img)

# Flag images
FLAG_SIZE = (20, 20)
YELLOW_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(YELLOW_FLAG, YELLOW, (0, 0, 5, 20))
pygame.draw.polygon(YELLOW_FLAG, YELLOW, [(5, 0), (20, 5), (5, 10)])

RED_FLAG = pygame.Surface(FLAG_SIZE, pygame.SRCALPHA)
pygame.draw.rect(RED_FLAG, RED, (0, 0, 5, 20))
pygame.draw.polygon(RED_FLAG, RED, [(5, 0), (20, 5), (5, 10)])

# Initialize screen (will be updated once map is loaded)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Courier Simulator")

# Font for UI
font = pygame.font.SysFont('Arial', 24)

# UI elements
button_width, button_height = 180, 40
button_spacing = 20
button_y = 20

# Button Positions
load_map_button_rect = pygame.Rect(20, button_y, button_width, button_height)
randomize_button_rect = pygame.Rect(20 + button_width + button_spacing, button_y, button_width, button_height)
start_button_rect = pygame.Rect(20 + (button_width + button_spacing) * 2, button_y, button_width, button_height)
reset_button_rect = pygame.Rect(20 + (button_width + button_spacing) * 3, button_y, button_width, button_height)

def calculate_road_centers():
    """Calculate road center positions using simple distance calculation"""
    global ROAD_CENTER_MAP
    
    if not MAP_LOADED:
        return
    
    height, width = MAP_ARRAY.shape
    ROAD_CENTER_MAP = np.zeros((height, width), dtype=float)
    
    # For each road pixel, calculate distance to nearest non-road pixel
    for y in range(height):
        for x in range(width):
            if MAP_ARRAY[y][x]:  # If it's a road pixel
                min_dist = float('inf')
                
                # Check in a reasonable radius
                for dy in range(-20, 21):
                    for dx in range(-20, 21):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < width and 0 <= ny < height):
                            if not MAP_ARRAY[ny][nx]:  # Non-road pixel
                                dist = (dx*dx + dy*dy) ** 0.5
                                min_dist = min(min_dist, dist)
                
                ROAD_CENTER_MAP[y][x] = min_dist if min_dist != float('inf') else 0

def load_map():
    """Load map image and process it to identify roads"""
    global MAP_LOADED, MAP_SURFACE, MAP_ARRAY, WIDTH, HEIGHT, screen
    
    root = Tk()
    root.withdraw()  # Hide the root window
    
    file_path = filedialog.askopenfilename(
        title="Select Map Image",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    
    if not file_path:
        return
    
    # Load map image
    try:
        map_img = pygame.image.load(file_path)
        map_width, map_height = map_img.get_size()
        
        # Ensure map meets size requirements
        if not (1000 <= map_width <= 1500 and 700 <= map_height <= 1000):
            print(f"Map size {map_width}x{map_height} outside allowed range")
            return
        
        # Resize window to match map size
        WIDTH, HEIGHT = map_width, map_height + 80  # Extra space for UI
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        # Create map surface and array
        MAP_SURFACE = map_img
        
        # Process map to identify roads
        map_array = pygame.surfarray.array3d(map_img)
        road_array = np.zeros((map_height, map_width), dtype=bool)
        
        # Identify road pixels (grayscale between R:90,G:90,B:90 and R:150,G:150,B:150)
        for y in range(map_height):
            for x in range(map_width):
                r, g, b = map_array[x][y]
                # Check if color is in road range and approximately equal RGB (gray)
                if (90 <= r <= 150 and 90 <= g <= 150 and 90 <= b <= 150 and
                    abs(r - g) <= 15 and abs(r - b) <= 15 and abs(g - b) <= 15):
                    road_array[y][x] = True
        
        MAP_ARRAY = road_array
        
        # Calculate road centers
        print("Calculating road centers...")
        calculate_road_centers()
        
        MAP_LOADED = True
        
        # Reset positions and path
        randomize_positions()
        reset_simulation()
        
        print(f"Map loaded: {file_path}")
        print(f"Map size: {map_width}x{map_height}")
        print(f"Roads identified: {np.sum(road_array)} pixels")
        
    except Exception as e:
        print(f"Error loading map: {e}")

def find_best_road_position(positions, min_center_distance=3):
    """Find positions that are closer to road centers"""
    if not MAP_LOADED or ROAD_CENTER_MAP is None:
        return positions
    
    best_positions = []
    for x, y in positions:
        if ROAD_CENTER_MAP[y][x] >= min_center_distance:
            best_positions.append((x, y))
    
    return best_positions if best_positions else positions

def randomize_positions():
    """Randomize courier, source, and destination positions on valid road tiles"""
    global COURIER_POS, SOURCE_POS, DEST_POS, COURIER_DIRECTION, HAS_PACKAGE, PATH
    
    if not MAP_LOADED:
        return
    
    # Get all road positions
    road_positions = np.argwhere(MAP_ARRAY)
    
    if len(road_positions) < 3:
        print("Not enough road positions found")
        return
    
    # Convert to (x, y) format and find center positions
    road_positions = [(x, y) for y, x in road_positions]
    center_positions = find_best_road_position(road_positions)
    
    # Use center positions if available, otherwise fallback to all road positions
    positions_to_use = center_positions if len(center_positions) >= 3 else road_positions
    
    # Shuffle positions
    random.shuffle(positions_to_use)
    
    # Select positions for courier, source, and destination
    COURIER_POS = (float(positions_to_use[0][0]), float(positions_to_use[0][1]))
    SOURCE_POS = positions_to_use[1]
    DEST_POS = positions_to_use[2]
    
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
    
    start_pos = (int(COURIER_POS[0]), int(COURIER_POS[1]))
    
    if not HAS_PACKAGE:
        # First path: courier to source
        target = SOURCE_POS
    else:
        # Second path: source to destination
        target = DEST_POS
    
    PATH = find_path(start_pos, target)
    CURRENT_PATH_INDEX = 0
    
    if not PATH:
        print(f"No path found to {'source' if not HAS_PACKAGE else 'destination'}")
        RUNNING = False

def find_path(start, end):
    """A* pathfinding algorithm with road center preference"""
    if not MAP_LOADED or not MAP_ARRAY[end[1]][end[0]] or not MAP_ARRAY[start[1]][start[0]]:
        return []
    
    # A* algorithm
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    
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
            path.append(current)
            path.reverse()
            
            # Smooth the path
            return smooth_path(path)
        
        # Check neighbors (8-way movement)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            x, y = current[0] + dx, current[1] + dy
            
            if (0 <= x < MAP_ARRAY.shape[1] and 0 <= y < MAP_ARRAY.shape[0] and 
                MAP_ARRAY[y][x]):
                
                neighbor = (x, y)
                
                # Movement cost (diagonal costs more)
                move_cost = 1.4 if abs(dx) + abs(dy) == 2 else 1.0
                
                # Road center preference (if available)
                road_bonus = 0
                if ROAD_CENTER_MAP is not None:
                    road_bonus = ROAD_CENTER_MAP[y][x] * 0.1
                
                tentative_g = g_score[current] + move_cost - road_bonus
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
    
    return []

def smooth_path(path):
    """Smooth path to reduce zigzag movement"""
    if len(path) <= 2:
        return path
    
    smoothed = [path[0]]
    i = 0
    
    while i < len(path) - 1:
        current = path[i]
        
        # Look ahead for straight line opportunities
        farthest = i + 1
        for j in range(i + 2, min(i + 8, len(path))):
            if can_move_straight(current, path[j]):
                farthest = j
            else:
                break
        
        if farthest > i + 1:
            smoothed.append(path[farthest])
            i = farthest
        else:
            smoothed.append(path[i + 1])
            i += 1
    
    return smoothed

def can_move_straight(start, end):
    """Check if we can move straight between two points"""
    x1, y1 = start
    x2, y2 = end
    
    steps = max(abs(x2 - x1), abs(y2 - y1))
    if steps == 0:
        return True
    
    for i in range(steps + 1):
        x = int(x1 + (x2 - x1) * i / steps)
        y = int(y1 + (y2 - y1) * i / steps)
        
        if not (0 <= x < MAP_ARRAY.shape[1] and 0 <= y < MAP_ARRAY.shape[0] and MAP_ARRAY[y][x]):
            return False
    
    return True

def heuristic(a, b):
    """Euclidean distance heuristic"""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def update_courier():
    """Update courier position along the path"""
    global COURIER_POS, COURIER_DIRECTION, HAS_PACKAGE, PATH, CURRENT_PATH_INDEX, RUNNING, FINISHED
    
    if not RUNNING or not PATH or CURRENT_PATH_INDEX >= len(PATH):
        return
    
    # Target position from path
    target_pos = PATH[CURRENT_PATH_INDEX]
    
    # Current position
    cx, cy = COURIER_POS
    tx, ty = target_pos
    
    # Calculate direction and distance
    dx = tx - cx
    dy = ty - cy
    distance = (dx ** 2 + dy ** 2) ** 0.5
    
    if distance < MOVEMENT_SPEED:
        # Reached waypoint, move to next
        COURIER_POS = (float(tx), float(ty))
        CURRENT_PATH_INDEX += 1
        
        # Check if completed path
        if CURRENT_PATH_INDEX >= len(PATH):
            courier_x, courier_y = int(COURIER_POS[0]), int(COURIER_POS[1])
            
            if not HAS_PACKAGE:
                # Check if at source
                if (abs(courier_x - SOURCE_POS[0]) < 10 and 
                    abs(courier_y - SOURCE_POS[1]) < 10):
                    HAS_PACKAGE = True
                    # Calculate path to destination
                    PATH = find_path((courier_x, courier_y), DEST_POS)
                    CURRENT_PATH_INDEX = 0
                    if not PATH:
                        RUNNING = False
                        print("No path to destination!")
            else:
                # Check if at destination
                if (abs(courier_x - DEST_POS[0]) < 10 and 
                    abs(courier_y - DEST_POS[1]) < 10):
                    RUNNING = False
                    FINISHED = True
                    print("Delivery complete!")
    else:
        # Move towards target
        dx /= distance
        dy /= distance
        
        new_x = cx + dx * MOVEMENT_SPEED
        new_y = cy + dy * MOVEMENT_SPEED
        COURIER_POS = (new_x, new_y)
        
        # Update direction
        if abs(dx) > abs(dy):
            COURIER_DIRECTION = 0 if dx > 0 else 2
        else:
            COURIER_DIRECTION = 1 if dy > 0 else 3

def draw_ui():
    """Draw UI elements"""
    # Draw buttons
    pygame.draw.rect(screen, BLUE, load_map_button_rect)
    pygame.draw.rect(screen, GREEN, randomize_button_rect)
    pygame.draw.rect(screen, YELLOW if not RUNNING else RED, start_button_rect)
    pygame.draw.rect(screen, GRAY, reset_button_rect)
    
    # Draw button text
    load_text = font.render("Load Map", True, WHITE)
    random_text = font.render("Randomize", True, WHITE)
    start_text = font.render("Start" if not RUNNING else "Pause", True, WHITE)
    reset_text = font.render("Reset", True, WHITE)
    
    screen.blit(load_text, (load_map_button_rect.x + 10, load_map_button_rect.y + 10))
    screen.blit(random_text, (randomize_button_rect.x + 10, randomize_button_rect.y + 10))
    screen.blit(start_text, (start_button_rect.x + 10, start_button_rect.y + 10))
    screen.blit(reset_text, (reset_button_rect.x + 10, reset_button_rect.y + 10))
    
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
    
    # Draw path with thicker line
    if PATH and len(PATH) > 1:
        for i in range(len(PATH) - 1):
            pygame.draw.line(screen, BLUE, 
                            (PATH[i][0], PATH[i][1] + 80), 
                            (PATH[i+1][0], PATH[i+1][1] + 80), 4)
    
    # Draw source and destination
    screen.blit(YELLOW_FLAG, (SOURCE_POS[0] - 10, SOURCE_POS[1] - 10 + 80))
    screen.blit(RED_FLAG, (DEST_POS[0] - 10, DEST_POS[1] - 10 + 80))
    
    # Draw courier
    courier_img = COURIER_IMGS[COURIER_DIRECTION]
    screen.blit(courier_img, (int(COURIER_POS[0]) - 10, int(COURIER_POS[1]) - 10 + 80))
    
    # Draw package indicator
    if HAS_PACKAGE:
        package_indicator = font.render("Has Package", True, GREEN)
        screen.blit(package_indicator, (WIDTH - 150, 20))

def main():
    """Main game loop"""
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
        screen.fill(WHITE)
        draw_ui()
        draw_game()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
