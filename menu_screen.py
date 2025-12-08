import displayio
import terminalio
from adafruit_display_text import label
import time

class MenuScreen:
    def __init__(self, display, encoder, button):
        self.display = display
        self.encoder = encoder
        self.button = button

        self.options = ["Easy", "Medium", "Hard"]
        self.index = 0

        # UI 显示组
        self.group = displayio.Group()

        # Title 居中
        self.title = label.Label(terminalio.FONT, text="Select Difficulty", x=5, y=10)
        self.group.append(self.title)

        # Arrow
        self.arrow = label.Label(terminalio.FONT, text=">", x=5, y=30)
        self.group.append(self.arrow)

        # Menu Options
        self.labels = []
        for i, txt in enumerate(self.options):
            lab = label.Label(terminalio.FONT, text=txt, x=20, y=30 + i * 12)
            self.labels.append(lab)
            self.group.append(lab)

    def draw(self):
        self.display.root_group = self.group

    def update(self):
        self.encoder.update()
        step = self.encoder.get_step()  # -1,0,+1

        if step != 0:
            self.index += step
            self.index = max(0, min(len(self.options)-1, self.index))
            self.arrow.y = 30 + self.index * 12

        if not self.button.value:  # pressed
            time.sleep(0.2)
            return self.options[self.index]

        return None
