from os.path import normpath, basename
from tkinter import *

from PIL import Image, ImageDraw, ImageTk, ImageFont

# Colors
BG_COLOR = 'black'
FG_COLOR = 'white'
NO_COLOR = ''

# Scale 128x64 to 480x240
SCALE = 240 / 128
OLED_WIDTH = 128
OLED_HEIGHT = 64
LED_HEIGHT = 10

def get_scaled_value(value):
    return round(value * SCALE)

class OLED(Canvas):
    line_mode = False
    show_info_bar = True

    def __init__(self, root):
        self.scaled_width = get_scaled_value(OLED_WIDTH)
        self.scaled_height = get_scaled_value(OLED_HEIGHT)
        self.scaled_height_with_led = get_scaled_value(OLED_HEIGHT + LED_HEIGHT)
        super().__init__(root, width=self.scaled_width, height=self.scaled_height_with_led, bg=BG_COLOR)

        self.image = Image.new('RGB', (self.scaled_width,self.scaled_height_with_led), BG_COLOR)
        self.draw = ImageDraw.Draw(self.image)
        self.tkimage = ImageTk.PhotoImage(self.image)
        self.image_id = self.create_image(0, 0, image=self.tkimage, anchor='nw')

        # Create lines
        self.oled_lines = []
        self.oled_line_boxes = []
        self.create_line_with_box(5, 20, '')
        self.create_line_with_box(5, 30, '')
        self.create_line_with_box(5, 40, '')
        self.create_line_with_box(5, 50, '')
        self.create_line_with_box(5, 60, '')

        # Create VU Meters
        self.vumeters = self.create_text(get_scaled_value(3), get_scaled_value(10),
                                         font=("Courier", get_scaled_value(6)),
                                         anchor='sw',
                                         text='I::::::::::: O:::::::::::',
                                         fill=FG_COLOR)

        self.master.after(100, self.refresh)

    def refresh(self):
        if self.winfo_ismapped():
            self.update()
        self.master.after(100, self.refresh)

    def create_line_with_box(self, x, y, text):
        box_id = self.create_rectangle(0,
                                       get_scaled_value(y - 5),
                                       get_scaled_value(132),
                                       get_scaled_value(y + 5),
                                       fill=NO_COLOR, outline=NO_COLOR)
        line_id = self.create_text(get_scaled_value(x),
                                   get_scaled_value(y),
                                   font=("Courier", get_scaled_value(6)),
                                   anchor='w', text=text, fill=FG_COLOR)
        self.oled_lines.append(line_id)
        self.oled_line_boxes.append(box_id)
        self.tag_lower(box_id, line_id)

    def add_osc_methods(self, server):
        # Register /oled/line/<number> from 1 to 5
        for i in range(1, 6):
            server.add_method('/oled/line/' + str(i), None, self.oled_line)

        # Register /oled/invertline <number> to highlight a line
        server.add_method('/oled/invertline', None, self.oled_invert_line)

        # Register graphics methods
        server.add_method('/oled/gClear', None, self.oled_g_clear)
        server.add_method('/oled/gSetPixel', None, self.oled_g_set_pixel)
        server.add_method('/oled/gLine', None, self.oled_g_line)
        server.add_method('/oled/gInvertArea', None, self.oled_g_invert_area)
        server.add_method('/oled/gFlip', None, self.oled_g_flip)
        server.add_method('/oled/gPrintln', None, self.oled_g_println)
        server.add_method('/oled/gBox', None, self.oled_g_box)
        server.add_method('/oled/gFillArea', None, self.oled_g_fill_area)
        server.add_method('/oled/gWaveform', None, self.oled_g_waveform)

        # Register vu meter method
        server.add_method('/oled/vumeter', None, self.oled_vumeter)
        server.add_method('/oled/gShowInfoBar', None, self.oled_g_show_info_bar)

        # Led
        server.add_method('/led', None, self.led)

    def oled_line(self, path, args, types, src):
        self.master.after(0, self._oled_line, path, args, types, src)

    def oled_invert_line(self, path, args, types, src):
        self.master.after(0, self._oled_invert_line, path, args, types, src)

    def oled_g_clear(self, path, args, types, src):
        self.master.after(0, self._oled_g_clear, path, args, types, src)

    def oled_g_set_pixel(self, path, args, types, src):
        self.master.after(0, self._oled_g_set_pixel, path, args, types, src)

    def oled_g_line(self, path, args, types, src):
        self.master.after(0, self._oled_g_line, path, args, types, src)

    def oled_g_invert_area(self, path, args, types, src):
        self.master.after(0, self._oled_g_invert_area, path, args, types, src)

    def oled_g_flip(self, path, args, types, src):
        self.master.after(0, self._oled_g_flip, path, args, types, src)

    def oled_vumeter(self, path, args, types, src):
        self.master.after(0, self._oled_vumeter, path, args, types, src)

    def oled_g_show_info_bar(self, path, args, types, src):
        self.master.after(0, self._oled_g_show_info_bar, path, args, types, src)

    def oled_g_println(self, path, args, types, src):
        self.master.after(0, self._oled_g_println, path, args, types, src)

    def oled_g_box(self, path, args, types, src):
        self.master.after(0, self._oled_g_box, path, args, types, src)

    def oled_g_fill_area(self, path, args, types, src):
        self.master.after(0, self._oled_g_fill_area, path, args, types, src)

    def oled_g_waveform(self, path, args, types, src):
        self.master.after(0, self._oled_g_waveform, path, args, types, src)

    def led(self, path, args, types, src):
        self.master.after(0, self._led, path, args, types, src)

    def _oled_line(self, path, args, types, src):
        if not self.line_mode:
            self._oled_g_clear(path, args, types, src)
            self._oled_g_flip(path, args, types, src)
            self.line_mode = True
            self.show_info_bar = True
        line = basename(normpath(path))
        index = int(line) - 1
        id = self.oled_lines[index]
        self.itemconfigure(id, text=args, fill=FG_COLOR)
        box_id = self.oled_line_boxes[index]
        self.itemconfigure(box_id, fill=NO_COLOR)

    def _oled_invert_line(self, path, args, types, src):
        index = int(args[0])
        for i in range(5):
            if i == index:
                bg = FG_COLOR
                fill = BG_COLOR
            else:
                bg = NO_COLOR
                fill = FG_COLOR
            line_id = self.oled_lines[i]
            self.itemconfigure(line_id, fill=fill)
            box_id = self.oled_line_boxes[i]
            self.itemconfigure(box_id, fill=bg)

    def _oled_g_clear(self, path, args, types, src):
        if self.line_mode:
            self.line_mode = False
        self.draw.rectangle((0, 0, self.scaled_width, self.scaled_height), fill=BG_COLOR)

    def _oled_g_flip(self, path, args, types, src):
        self.tkimage = ImageTk.PhotoImage(self.image)
        self.itemconfigure(self.image_id, image=self.tkimage)

    def _oled_g_set_pixel(self, path, args, types, src):
        x = int(args[1])
        y = int(args[2])
        if int(args[3]):
            color = FG_COLOR
        else:
            color = BG_COLOR
        self.set_scaled_pixel(x, y, color)

    def _oled_g_line(self, path, args, types, src):
        print("%s " % path, flush=True)
        for a, t in zip(args, types):
            print(a, sep=' ', end=' ', flush=True)
        print("")
        x1 = get_scaled_value(int(args[1]))
        y1 = int(args[2])
        if y1 < 0:
            y1 = 64 + y1
        y1 = get_scaled_value(y1)
        x2 = get_scaled_value(int(args[3]))
        y2 = int(args[4])
        if y2 < 0:
            y2 = 64 + y2
        y2 = get_scaled_value(y2)
        if int(args[5]):
            color = FG_COLOR
        else:
            color = BG_COLOR
        self.draw.line((x1, y1, x2, y2), color)
        self._oled_g_flip(path, args, types, src)

    def _oled_g_invert_area(self, path, args, types, src):
        #print("%s " % path, flush=True)
        #for a, t in zip(args, types):
        #    print(a, sep=' ', end=' ', flush=True)
        #print("")
        x1 = int(args[1])
        if x1 < 0: return
        x1 = get_scaled_value(x1)
        y1 = int(args[2])
        if y1 < 0: return
        y1 = get_scaled_value(y1)
        x2 = get_scaled_value(int(args[3]))
        y2 = get_scaled_value(int(args[4]))
        for i in range(x1, x1 + x2):
            for j in range(y1, y1 + y2):
                pixel = self.image.getpixel((i, j))
                if pixel == (0, 0, 0):
                    color = (255, 255, 255) #FG_COLOR
                else:
                    color = (0, 0, 0) #BG_COLOR
                self.draw.point((i, j), fill=color)

    def _oled_vumeter(self, path, args, types, src):
        if not self.show_info_bar:
            return

        inL = int(args[0])
        if inL < 0: inL = 0
        inR = int(args[1])
        if inR < 0: inR = 0
        outL = int(args[2])
        if outL < 0: outL = 0
        outR = int(args[3])
        if outR < 0: outR = 0

        text = "I"
        for i in range(11):
            if inL > i and inR > i:
                text = text + chr(9608)
            elif inL > i:
                text = text + chr(9600)
            elif inR > i:
                text = text + chr(9604)
            else:
                text = text + ":"

        text = text + " O"
        for i in range(11):
            if outL > i and outR > i:
                text = text + chr(9608)
            elif outL > i:
                text = text + chr(9600)
            elif outR > i:
                text = text + chr(9604)
            else:
                text = text + ":"

        self.itemconfigure(self.vumeters, text=text)

    def _oled_g_show_info_bar(self, path, args, types, src):
        if int(args[1]):
            self.show_info_bar = True
        else:
            self.show_info_bar = False
        self.itemconfigure(self.vumeters, text='')

    def _oled_g_println(self, path, args, types, src):
        if self.line_mode:
            self.line_mode = False
        x = get_scaled_value(int(args[1]))
        y = get_scaled_value(int(args[2]))
        size = get_scaled_value(int(args[3]))
        if int(args[4]):
            color = FG_COLOR
        else:
            color = BG_COLOR
        text = ''
        for s in args[5:]:
            text = text + s + ' '
        font = ImageFont.truetype('Courier.ttf', size)
        self.draw.text((x, y), text, color, font, align='left')
        self._oled_g_flip(path, args, types, src)

    def _oled_g_box(self, path, args, types, src):
        x1 = int(args[1])
        if x1 < 0:
            x1 = 0
        x1 = get_scaled_value(x1)
        y1 = int(args[2])
        if y1 < 0:
            y1 = 64 + y1
        y1 = get_scaled_value(y1)
        x2 = int(args[3])
        if x2 < 0:
            x2 = 0
        x2 = get_scaled_value(x2)
        y2 = int(args[4])
        if y2 < 0:
            y2 = 64 + y2
        y2 = get_scaled_value(y2)
        if int(args[5]):
            color = FG_COLOR
        else:
            color = BG_COLOR
        self.draw.line((x1, y1, x1 + x2, y1, x1 + x2, y1 + y2, x1, y1 + y2, x1, y1), color, get_scaled_value(1))

    def _oled_g_fill_area(self, path, args, types, src):
        x1 = get_scaled_value(int(args[1]))
        y1 = int(args[2])
        if y1 < 0:
            y1 = OLED_HEIGHT + y1
        y1 = get_scaled_value(y1)
        x2 = get_scaled_value(int(args[3]))
        y2 = int(args[4])
        if y2 < 0:
            y2 = OLED_HEIGHT + y2
        y2 = get_scaled_value(y2)
        if int(args[5]):
            color = FG_COLOR
        else:
            color = BG_COLOR
        self.draw.rectangle((x1, y1, x1 + x2, y1 + y2), color)

    def _oled_g_waveform(self, path, args, types, src):
        blob = args[1]
        bloblen = len(blob)
        if bloblen > 128:
            bloblen = 128
        for i in range(1, bloblen):
            x1 = get_scaled_value(i - 1)
            y1 = get_scaled_value(blob[i - 1] & 0x3f)
            x2 = get_scaled_value(i)
            y2 = get_scaled_value(blob[i] & 0x3f)
            self.draw.line((x1, y1, x2, y2), FG_COLOR, width=get_scaled_value(1))

    def set_scaled_pixel(self, x, y, color):
        scaledx = get_scaled_value(x)
        scaledy = get_scaled_value(y)
        scaledx2 = scaledx + SCALE - 1
        scaledy2 = scaledy + SCALE - 1
        self.draw.rectangle((scaledx, scaledy, scaledx2, scaledy2), fill=color)

    def _led(self, path, args, types, src):
        value = int(args[0])
        if value == 1:
            color = 'green'
        elif value == 2:
            color = 'blue'
        elif value == 3:
            color = 'aqua'
        elif value == 4:
            color = 'red'
        elif value == 5:
            color = 'yellow'
        elif value == 6:
            color = (255,52,179)
        elif value == 7:
            color = 'white'
        else:
            color = 'black'
        self.draw.rectangle((0, self.scaled_height, self.scaled_width, self.scaled_height_with_led), color)
        self._oled_g_flip(path, args, types, src)
