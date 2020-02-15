##
 #  @filename   :   main.cpp
 #  @brief      :   4.2inch e-paper display (B) demo
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     August 15 2017
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 ##

from . import epd4in2b
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import threading
import queue


# Clock Display Class - takes care of the display.
class ClockDisplay(threading.Thread):

    # Initialising - set up the display, fonts, etc.
    def __init__(self):
        threading.Thread.__init__(self)

        self.epd = epd4in2b.EPD()
        self.epd.init()
        self.image_red = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)    # 255: clear the frame
        self.draw_red = ImageDraw.Draw(self.image_red)
        self.image_black = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)    # 255: clear the frame
        self.draw_black = ImageDraw.Draw(self.image_black)
        self.date_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 45)
        self.time_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 100)
        self.time_queue = queue.Queue()

    # Main process of the thread.  Waits for the criteria to be reached for the displaying on the screen.
    def run(self):

        while True:

            if not self.time_queue.empty():
                time_to_display = self.time_queue.get_nowait()
                self.image_red = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)  # 255: clear the frame
                self.draw_red = ImageDraw.Draw(self.image_red)
                self.image_black = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)  # 255: clear the frame
                self.draw_black = ImageDraw.Draw(self.image_black)
                print (time_to_display)
                self.display_time(time_to_display)
                self.write_display()

            time.sleep(2)

    # Displays date and time on the screen
    def display_time(self, time_to_display):
        self.draw_black.text((0, 10), time.strftime("%a %d %m %Y", time_to_display), font = self.date_font, fill = 0)
        self.draw_red.text((50, 40), time.strftime("%H:%M", time_to_display), font=self.time_font, fill=0)

    # Writes the display frames to the display.
    def write_display(self):
        # display the frames
        self.epd.display_frame(self.epd.get_frame_buffer(self.image_black), self.epd.get_frame_buffer(self.image_red))


if __name__ == '__main__':
    clock_display = ClockDisplay(1)
    clock_display.start()
    #clock_display.display_time(time.localtime())
    #clock_display.write_display()
