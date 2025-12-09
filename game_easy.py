# game_easy.py - Complete English Version with NeoPixel support
import time
import board
import digitalio
import displayio
import i2cdisplaybus
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import terminalio
import json

# Load Level Data from JSON 
def load_levels(difficulty="easy"):
    """Load level data from levels.json file"""
    try:
        with open('levels.json', 'r') as f:
            data = json.load(f)
            levels = data['levels']
            game_settings = data['game_settings']
            
            # Adjust difficulty
            if difficulty == "medium":
                for level in levels:
                    for obs in level.get('obstacles', []):
                        obs['speed'] = obs.get('speed', 1.5) * 1.3
            elif difficulty == "hard":
                for level in levels:
                    for obs in level.get('obstacles', []):
                        obs['speed'] = obs.get('speed', 1.5) * 1.6
            
            return levels, game_settings
    except Exception as e:
        print(f"Error loading levels.json: {e}")
        return [
            {
                "level": 1,
                "name": "Tutorial",
                "obstacles": [{"x": 128, "speed": 1.5}],
                "message": "Jump over 1 spaceship!"
            }
        ], {
            "jump_height": 28,
            "jump_duration": 20,
            "ground_y": 50,
            "player_x": 10
        }

def run_game(display, button, accel_monitor=None, difficulty="easy"):
    """Main game function - called from main.py"""
    
    LEVELS, GAME_SETTINGS = load_levels(difficulty)
    print(f"Loaded {len(LEVELS)} levels from configuration ({difficulty} mode)")
    
    # Create new display group
    main_group = displayio.Group()
    display.root_group = main_group
    
    # Constants / State
    ground_y = GAME_SETTINGS.get('ground_y', 50)
    player_x = GAME_SETTINGS.get('player_x', 10)
    player_width = 11
    player_height = 11
    jump_height = GAME_SETTINGS.get('jump_height', 28)
    jump_duration = GAME_SETTINGS.get('jump_duration', 40)
    obstacle_width = 12
    obstacle_height = 8
    
    # Player Star 11x11 Bitmap
    player_bitmap = displayio.Bitmap(11, 11, 2)
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0xFFFFFF
    
    star_pattern = [
        0,0,0,0,0,1,0,0,0,0,0,
        0,0,0,0,1,1,1,0,0,0,0,
        0,0,0,0,1,1,1,0,0,0,0,
        0,0,0,1,0,1,0,1,0,0,0,
        0,1,1,0,0,1,0,0,1,1,0,
        1,1,1,1,1,1,1,1,1,1,1,
        0,1,1,1,1,1,1,1,1,1,0,
        0,0,1,1,1,0,1,1,1,0,0,
        0,0,1,1,0,0,0,1,1,0,0,
        0,1,1,0,0,0,0,0,1,1,0,
        0,1,0,0,0,0,0,0,0,1,0
    ]
    for y in range(11):
        for x in range(11):
            player_bitmap[x, y] = star_pattern[y*11 + x]
    
    player_tile = displayio.TileGrid(player_bitmap, pixel_shader=palette, x=player_x, y=ground_y)
    main_group.append(player_tile)
    
    # Obstacle Bitmap
    obstacle_bitmap = displayio.Bitmap(12, 8, 2)
    
    spaceship_pattern = [
        0,0,0,0,1,1,1,0,0,0,0,0,
        0,0,0,1,1,1,1,1,0,0,0,0,
        0,0,1,1,1,1,1,1,1,0,0,0,
        0,1,1,1,1,1,1,1,1,1,1,0,
        1,1,1,1,1,1,1,1,1,1,1,1,
        0,1,1,1,1,1,1,1,1,1,1,0,
        0,0,1,1,1,1,1,1,1,0,0,0,
        0,0,0,1,1,1,0,0,1,1,0,0
    ]
    for oy in range(8):
        for ox in range(12):
            obstacle_bitmap[ox, oy] = spaceship_pattern[oy * 12 + ox]
    
    obstacle_y = ground_y + player_height - obstacle_height
    
    max_obstacles = max(len(level['obstacles']) for level in LEVELS)
    obstacles = []
    for i in range(max_obstacles):
        obs_tile = displayio.TileGrid(obstacle_bitmap, pixel_shader=palette, x=300, y=obstacle_y)
        main_group.append(obs_tile)
        obstacles.append({
            'tile': obs_tile, 
            'x': 300.0, 
            'speed': 1.5,
            'can_jump': False,
            'jumping': False,
            'jump_timer': 0,
            'jump_duration': 20,
            'jump_height': 15,
            'base_y': obstacle_y
        })
    
    # Score and Game Status
    current_level_index = 0
    obstacles_cleared = 0
    game_won = False
    
    def get_current_level():
        """Get current level data"""
        if current_level_index >= len(LEVELS):
            return LEVELS[-1]
        return LEVELS[current_level_index]
    
    def load_level(level_data):
        """Load level configuration"""
        nonlocal jump_height, jump_duration
        if 'jump_height' in level_data:
            jump_height = level_data['jump_height']
        if 'jump_duration' in level_data:
            jump_duration = level_data['jump_duration']
        
        for i, obs in enumerate(obstacles):
            if i < len(level_data['obstacles']):
                obs_data = level_data['obstacles'][i]
                obs['x'] = float(obs_data['x'])
                obs['speed'] = obs_data.get('speed', 1.5)
                obs['tile'].x = int(obs['x'])
                obs['can_jump'] = obs_data.get('jumping', False)
                obs['jumping'] = False
                obs['jump_timer'] = 0
                y_offset = obs_data.get('y_offset', 0)
                obs['base_y'] = obstacle_y + y_offset
                obs['tile'].y = obs['base_y']
            else:
                obs['x'] = 500.0
                obs['tile'].x = 500
                obs['can_jump'] = False
                obs['base_y'] = obstacle_y
    
    level_data = get_current_level()
    load_level(level_data)
    
    score_label = label.Label(terminalio.FONT,
                             text=f"Lv{level_data['level']}:{level_data['name']}",
                             color=0xFFFFFF, x=0, y=5)
    main_group.append(score_label)
    
    game_over_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=15, y=35)
    main_group.append(game_over_label)
    
    # Game State Variables 
    jumping = False
    jump_timer = 0
    game_over = False
    prev_button_state = True
    
    debug = True
    print(f"=== Star Jump Game ({difficulty.upper()}) ===")
    
    # Main Game Loop
    while True:
        # Game Over Handling
        if game_over:
            # Turn on red light on Game Over
            if accel_monitor:
                accel_monitor.set_red()
            
            game_over_label.text = "GAME OVER"
            game_over_label.x = 38
            time.sleep(1.8)
            
            game_over_label.text = "click to restart"
            game_over_label.x = 5
            time.sleep(1)
            
            if not button.value:
                # Clear red light when restarting
                if accel_monitor:
                    accel_monitor.clear_override()
                
                game_over = False
                game_won = False
                obstacles_cleared = 0
                
                level_data = get_current_level()
                load_level(level_data)
                
                game_over_label.text = ""
                score_label.text = f"Lv{level_data['level']}:{level_data['name']}"
                
                print("Restarting CURRENT LEVEL!")
            
            time.sleep(0.1)
            continue
        
        # Level Complete Handling
        if game_won:
            if current_level_index >= 9:
                game_over_label.text = "CONGRATS!"
                game_over_label.x = 38
                time.sleep(2)
                
                game_over_label.text = "It's the time"
                game_over_label.x = 10
                time.sleep(3)
                
                game_over_label.text = "Return to your world."
                game_over_label.x = 0
                time.sleep(3)
                
                game_over_label.text = "life still goes on"
                game_over_label.x = 5
                time.sleep(3)
                
                print("All levels finished.")
                break  # Exit game, return to main menu
            
            game_over_label.text = "GOOD JOB!"
            game_over_label.x = 38
            time.sleep(2)
            
            current_level_index += 1
            obstacles_cleared = 0
            game_won = False
            game_over_label.text = ""
            
            level_data = get_current_level()
            load_level(level_data)
            score_label.text = f"Lv{level_data['level']}:{level_data['name']}"
            print(f"Next Level {level_data['level']}")
            time.sleep(0.5)
            continue
        
        # Button Input
        button_pressed = not button.value
        button_just_pressed = (not prev_button_state and button_pressed)
        prev_button_state = button_pressed
        
        if button_just_pressed and not jumping:
            jumping = True
            jump_timer = jump_duration
            if debug:
                print("JUMP!")
        
        # Jump Animation
        if jumping:
            progress = 1 - (jump_timer / jump_duration)
            height = jump_height * (1 - (2 * progress - 1) ** 2)
            player_tile.y = int(ground_y - height)
            
            jump_timer -= 1
            if jump_timer <= 0:
                jumping = False
                player_tile.y = ground_y
        
        # Obstacle Movement
        level_data = get_current_level()
        active_obstacles = obstacles[:len(level_data['obstacles'])]
        
        for obs in active_obstacles:
            obs['x'] -= obs['speed']
            obs['tile'].x = int(obs['x'])
            
            # Obstacle Jumping (Hard Mode)
            if obs.get('can_jump', False):
                if not obs['jumping'] and obs['x'] < 90 and obs['x'] > 60:
                    obs['jumping'] = True
                    obs['jump_timer'] = obs['jump_duration']
                
                if obs['jumping']:
                    progress = 1 - (obs['jump_timer'] / obs['jump_duration'])
                    height = obs['jump_height'] * (1 - (2 * progress - 1) ** 2)
                    obs['tile'].y = int(obs['base_y'] - height)
                    
                    obs['jump_timer'] -= 1
                    if obs['jump_timer'] <= 0:
                        obs['jumping'] = False
                        obs['tile'].y = obs['base_y']
            
            if obs['x'] < -obstacle_width:
                obstacles_cleared += 1
                obs['x'] = 128 + len(active_obstacles)*70
                obs['jumping'] = False
                obs['jump_timer'] = 0
                obs['tile'].y = obs['base_y']
                
                if obstacles_cleared >= len(active_obstacles):
                    game_won = True
        
        # Collision Detection
        collision = False
        
        for obs in active_obstacles:
            player_left = player_x + 3
            player_right = player_x + player_width - 3
            player_top = player_tile.y + 2
            player_bottom = player_tile.y + player_height - 2
            
            obs_left = int(obs['x']) + 2
            obs_right = int(obs['x']) + obstacle_width - 2
            obs_top = obs['tile'].y + 1
            obs_bottom = obs['tile'].y + obstacle_height - 1
            
            if (player_right > obs_left and player_left < obs_right and
                player_bottom > obs_top and player_top < obs_bottom):
                collision = True
                break
        
        if collision:
            game_over = True
            print("Game Over!")
        
        time.sleep(0.03)

# For standalone testing
if __name__ == "__main__":
    import board
    import busio
    import displayio
    import i2cdisplaybus
    import adafruit_displayio_ssd1306
    import digitalio
    
    displayio.release_displays()
    i2c_bus = board.I2C()
    display_bus = i2cdisplaybus.I2CDisplayBus(i2c_bus, device_address=0x3c)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
    
    button = digitalio.DigitalInOut(board.D1)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    
    run_game(display, button, difficulty="easy")
