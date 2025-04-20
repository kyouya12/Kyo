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
COURIER_POS = (0, 0)
SOURCE_POS = (0, 0)
DEST_POS = (0, 0)
COURIER_DIRECTION = 0  # 0: right, 1: down, 2: left, 3: up
HAS_PACKAGE = False
PATH = []
CURRENT_PATH_INDEX = 0
MOVEMENT_SPEED = 5  # pixels per frame
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
        MAP_LOADED = True
        
        # Reset positions and path
        randomize_positions()
        reset_simulation()
        
        print(f"Map loaded: {file_path}")
        print(f"Map size: {map_width}x{map_height}")
        print(f"Roads identified: {np.sum(road_array)} pixels")
        
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
        print("Not enough road positions found")
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
    
    # Draw path
    if PATH:
        for i in range(len(PATH) - 1):
            pygame.draw.line(screen, BLUE, 
                            (PATH[i][0], PATH[i][1] + 80), 
                            (PATH[i+1][0], PATH[i+1][1] + 80), 2)
    
    # Draw source and destination
    screen.blit(YELLOW_FLAG, (SOURCE_POS[0] - 10, SOURCE_POS[1] - 10 + 80))
    screen.blit(RED_FLAG, (DEST_POS[0] - 10, DEST_POS[1] - 10 + 80))
    
    # Draw courier
    courier_img = COURIER_IMGS[COURIER_DIRECTION]
    screen.blit(courier_img, (COURIER_POS[0] - 10, COURIER_POS[1] - 10 + 80))
    
    # Draw package indicator
    if HAS_PACKAGE:
        package_indicator = font.render("Has Package", True, GREEN)
        screen.blit(package_indicator, (WIDTH - 150, 20))

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
        screen.fill(WHITE)
        draw_ui()
        draw_game()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()