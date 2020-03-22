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

class LineStatus:

    def __init__(self):
        self.line_list = [ ["Bakerloo", "BAK", "None"],
                           ["Central", "CEN", "None"],
                           ["Circle", "CIR", "None"],
                           ["District", "DIS", "None"],
                           ["Hammersmith & City", "H&C", "None"],
                           ["Jubilee", "JUB", "None"],
                           ["Metropolitan", "MET", "None"],
                           ["Northern", "NOR", "None"],
                           ["Piccadilly", "PIC", "None"],
                           ["Waterloo & City", "W&C", "None"],
                           ["Victoria", "VIC", "None"]
                           ]

        self.abbrev_status = {"Good Service": "OK", "Part Closure": "P.CLS", "Special Service": "SPEC",
                              "Severe Delay": "SEV.D", "Minor Delays": "MIN.D", "Planned Closure": "CLS",
                              "Service Closed": "CLS", "Part Suspended": "P.SUS", "Suspended": "SUS"}

    # Fill out the line status, using abbreviations as possible.
    def fill_line_status(self, tfl_status_dict):

        # Go through all the status in the tfl status dictionary, replace lines and status with abbrev
        for line in tfl_status_dict:

            for i in range(len(self.line_list)):
                if line == self.line_list[i][0]:
                    # Check for Abbrev - use if available, otherwise don't change it.
                    if tfl_status_dict[line] in self.abbrev_status:
                        self.line_list[i][2] = self.abbrev_status[tfl_status_dict[line]]
                    else:
                        self.line_list[i][2] = tfl_status_dict[line]
                    break


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
        self.date_font = ImageFont.truetype('./display/HammersmithOne-Regular.ttf', 35)
        self.time_font = ImageFont.truetype('./display/HammersmithOne-Regular.ttf', 100)
        self.status_font = ImageFont.truetype('./display/HammersmithOne-Regular.ttf', 30)

        self.time_queue = queue.Queue()
        self.tfl_status_queue = queue.Queue()
        self.tfl_status_str = None

    # Main process of the thread.  Waits for the criteria to be reached for the displaying on the screen.
    def run(self):

        tfl_status_dict = None

        line_status = LineStatus()

        while True:

            if not self.time_queue.empty():
                time_to_display = self.time_queue.get_nowait()

                self.image_red = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)  # 255: clear the frame
                self.draw_red = ImageDraw.Draw(self.image_red)
                self.image_black = Image.new('1', (epd4in2b.EPD_WIDTH, epd4in2b.EPD_HEIGHT), 255)  # 255: clear the frame
                self.draw_black = ImageDraw.Draw(self.image_black)

                while not self.tfl_status_queue.empty():
                    tfl_status_dict = self.tfl_status_queue.get_nowait()

                shift = 0  # used to move the text along as move on to next status.

                if tfl_status_dict is not None:
                    line_status.fill_line_status(tfl_status_dict)

                    x_align =0
                    status_num =0

                    for item in line_status.line_list:
                        status_str = '{} {}' .format(item[1],  item[2])

                        if item[2] == "OK":
                            image = self.image_black
                        else:
                            image = self.image_red

                        self.draw_text((190 - shift, x_align), self.status_font, status_str, image, rotation=270)
                        shift += 35
                        status_num += 1
                        if status_num == 6:
                            x_align = 150
                            shift = 0

                #print (time_to_display)
                self.display_time(time_to_display)
                self.write_display()


            time.sleep(1)

    # Displays dte and time on the screen
    def display_time(self, time_to_display):
        date_str = time.strftime("%a %d %m %Y", time_to_display)
        w, h = self.date_font.getsize(date_str)
        print("date size", w, h)
        date_offset = int((epd4in2b.EPD_HEIGHT - w)/2)  # Calculate offset to center text.
        self.draw_text((370, date_offset), self.date_font, date_str, self.image_black, rotation=270)

        time_str = time.strftime("%H:%M", time_to_display)
        w, h = self.time_font.getsize(time_str)
        print("time size", w, h)
        time_offset = int((epd4in2b.EPD_HEIGHT - w)/2)  # Calculate offset to center text
        self.draw_text((300, time_offset), self.time_font, time_str, self.image_red, rotation=270)

    # Writes the display frames to the display.
    def write_display(self):
        # display the frames
        self.epd.display_frame(self.epd.get_frame_buffer(self.image_black), self.epd.get_frame_buffer(self.image_red))

    # Rotates the text - allows to write text portrait or whatever.
    def draw_text(self, position, font, text, image_red_or_black, rotation=0):
        w, h = font.getsize(text)
        mask = Image.new('1', (w, h), color=1)
        draw = ImageDraw.Draw(mask)
        draw.text((0, 0), text, 0, font)
        mask = mask.rotate(rotation, expand=True)
        image_red_or_black.paste(mask, position)

    #draw_text((20, 20), "Hello", colour=inkyphat.RED, rotation=45)
    #draw_text((80, 20), "World", rotation=90)

    #inkyphat.show()


if __name__ == '__main__':
    clock_display = ClockDisplay(1)
    clock_display.start()
    #clock_display.display_time(time.localtime())
    #clock_display.write_display()
