# main.py

# main.py
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

# ===== 设置显示屏 =====
displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# ===== 按钮设置 =====
button = digitalio.DigitalInOut(board.D6)
button.switch_to_input(pull=digitalio.Pull.UP)

# ===== 旋转编码器设置 =====
encoder = RotaryEncoder(board.D9, board.D8)

# ===== Intro 文本 =====
intro_lines = [
    "Hello",
    "You awake?",
    "It's year of 3035",
    "Remember?",
    "Time changed."
]

def wrap_text(text, max_chars=20):
    """文本换行函数"""
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
    """显示开场动画"""
    intro_group = displayio.Group()
    display.root_group = intro_group
    intro_label = label.Label(terminalio.FONT, text="", x=10, y=20)
    intro_group.append(intro_label)
    
    current_intro = 0
    last_button = True
    intro_label.text = wrap_text(intro_lines[current_intro])
    
    while True:
        current_state = button.value
        if last_button and not current_state:
            current_intro += 1
            if current_intro >= len(intro_lines):
                return  # 完成intro
            intro_label.text = wrap_text(intro_lines[current_intro])
            time.sleep(0.2)
        last_button = current_state
        time.sleep(0.01)

def show_menu():
    """显示难度选择菜单"""
    menu = MenuScreen(display, encoder, button)
    last_button = False
    
    while True:
        menu.draw()
        result = menu.update()
        current_state = button.value
        
        if result and last_button and not current_state:
            print("Selected difficulty:", result)
            return result  # 返回选择的难度
        
        last_button = current_state
        time.sleep(0.01)

def start_game(difficulty):
    """根据难度启动游戏"""
    print(f"Starting game with difficulty: {difficulty}")
    
    # 根据难度选择不同的levels.json文件或配置
    if difficulty == "Easy":
        from game_easy import run_game
        run_game(display, button)
    
    elif difficulty == "Medium":
        # 可以加载不同的配置或使用不同的参数
        print("Medium mode - using game_easy with modified settings")
        from game_easy import run_game
        run_game(display, button, difficulty="medium")
    
    elif difficulty == "Hard":
        print("Hard mode - using game_easy with hard settings")
        from game_easy import run_game
        run_game(display, button, difficulty="hard")
    
    else:
        print("Unknown difficulty")
        time.sleep(2)

def main():
    """主程序循环"""
    while True:
        # 1. 显示开场动画
        show_intro()
        
        # 2. 显示难度选择菜单
        selected_difficulty = show_menu()
        
        # 3. 启动对应难度的游戏
        start_game(selected_difficulty)
        
        # 游戏结束后显示结束画面
        end_group = displayio.Group()
        display.root_group = end_group
        end_label = label.Label(
            terminalio.FONT, 
            text="Thanks for\nplaying!\n\nPress to\nrestart", 
            x=20, 
            y=15
        )
        end_group.append(end_label)
        
        # 等待按钮按下重新开始
        last_button = button.value
        while True:
            current_state = button.value
            if last_button and not current_state:
                break
            last_button = current_state
            time.sleep(0.01)
        
        time.sleep(0.3)  # 防抖

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
