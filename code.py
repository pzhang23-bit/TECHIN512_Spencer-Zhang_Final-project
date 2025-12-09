# code.py
#Process: intro-words, 2. select mode 3.enter the games.
import time
import board
import digitalio
import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
from rotary_encoder import RotaryEncoder
from menu_screen import MenuScreen
from accel_monitor import AccelMonitor

# Display Setup
displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Accelerometer Monitor Setup
accel_monitor = AccelMonitor(i2c,neopixel_pin=board.D10, num_pixels=8, brightness=0.3)

# Button for menu (D6)
button = digitalio.DigitalInOut(board.D6)
button.switch_to_input(pull=digitalio.Pull.UP)

# Rotary Encoder Setup
encoder = RotaryEncoder(board.D9, board.D8)

# Intro Lines
intro_lines = [
    "Hello",
    "You awake?",
    "It's year of 3035",
    "Remember?",
    "Time changed."
]

def wrap_text(text, max_chars=20):
    """Text wrapping function"""
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        if len(current + " " + w) <= max_chars:
            if current:
                current += " " + w
            else:
                current = w
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return "\n".join(lines)

def show_intro():
    """Display intro animation"""
    intro_group = displayio.Group()
    display.root_group = intro_group
    intro_label = label.Label(terminalio.FONT, text="", x=10, y=20)
    intro_group.append(intro_label)
    
    current_intro = 0
    last_button = True
    intro_label.text = wrap_text(intro_lines[current_intro])
    
    while True:
        accel_monitor.update()
        
        current_state = button.value
        if last_button and not current_state:
            current_intro += 1
            if current_intro >= len(intro_lines):
                return  # Intro complete
            intro_label.text = wrap_text(intro_lines[current_intro])
            time.sleep(0.2)
        last_button = current_state
        time.sleep(0.01)

def show_menu():
    """Menu selection"""
    menu = MenuScreen(display, encoder, button)
    last_button = False
    
    while True:
        accel_monitor.update()
        
        menu.draw()
        result = menu.update()
        current_state = button.value
        
        if result and last_button and not current_state:
            print("Selected difficulty:", result)
            return result  # Return selected difficulty
        
        last_button = current_state
        time.sleep(0.01)

def start_game(difficulty):
    """Start game based on difficulty"""
    print(f"Starting game with difficulty: {difficulty}")
    
    # Create D1 button for game
    game_button = digitalio.DigitalInOut(board.D1)
    game_button.switch_to_input(pull=digitalio.Pull.UP)
    
    # Turn off pickup detection during game (game controls the lights)
    accel_monitor.clear_override()
    
    # Select different configurations based on difficulty
    if difficulty == "Easy":
        from game_easy import run_game
        run_game(display, game_button, accel_monitor)
    
    elif difficulty == "Medium":
        print("Medium mode - using game_easy with modified settings")
        from game_easy import run_game
        run_game(display, game_button, accel_monitor, difficulty="medium")
    
    elif difficulty == "Hard":
        print("Hard mode - using game_easy with hard settings")
        from game_easy import run_game
        run_game(display, game_button, accel_monitor, difficulty="hard")
    
    else:
        print("Unknown difficulty")
        time.sleep(2)

def main():
    """Main program loop"""
    while True:
        # 1. Intro
        show_intro()
        
        # 2. Menu Selection
        selected_difficulty = show_menu()
        
        # 3. Start Game
        start_game(selected_difficulty)
        
        # Ending Screen
        end_group = displayio.Group()
        display.root_group = end_group
        end_label = label.Label(
            terminalio.FONT, 
            text="Thanks for\nplaying!\n\nPress to\nrestart", 
            x=20, 
            y=15
        )
        end_group.append(end_label)
        
        # Wait for restart
        last_button = button.value
        while True:
            accel_monitor.update()
            
            current_state = button.value
            if last_button and not current_state:
                break
            last_button = current_state
            time.sleep(0.01)
        
        time.sleep(0.3)  # Debounce

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
        accel_monitor.off()
