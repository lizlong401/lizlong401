"""Render a seamless ASCII kinetic field. Run with Python and Pillow."""
from PIL import Image, ImageDraw, ImageFont
import math
from pathlib import Path

COLS, ROWS = 144, 60
CW, CH = 8, 13
COUNT = 80
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 12)
# All marks are ASCII; their density and angle suggest flipping elements.
marks = ' .:-=+*#%@'
background = (13, 15, 17)
frames = []
for frame in range(COUNT):
    t = frame / COUNT * math.tau
    canvas = Image.new('RGB', (COLS*CW, ROWS*CH), background)
    draw = ImageDraw.Draw(canvas)
    for row in range(ROWS):
        for col in range(COLS):
            x = (col-(COLS-1)/2)/31
            y = (row-(ROWS-1)/2)/23
            # Traveling folds with a slow twisting center and concentric wake.
            bend = 0.50*math.sin(x*1.5-t) + 0.20*math.cos(x*2+t)
            yy = y-bend
            radius = math.sqrt(x*x*0.58+yy*yy)
            a = math.atan2(yy,x)
            carrier = math.sin(yy*9 + 1.8*math.sin(x*2-t) + t*2)
            wake = math.cos(radius*10-t*2+0.8*math.sin(a*2+t))
            envelope = math.exp(-0.22*x*x-0.68*y*y)
            value = max(0,min(1,(0.5+0.34*carrier+0.16*wake)*envelope))
            idx = min(len(marks)-1,int(value*len(marks)))
            char = marks[idx]
            if char == ' ': continue
            brightness = int(65+value*184)
            draw.text((col*CW,row*CH),char,font=font,fill=(brightness,brightness,min(255,brightness+4)))
    frames.append(canvas.quantize(colors=32))
frames[0].save('assets/kinetic.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=2)
frames[20].convert('RGB').save('/tmp/z-kinetic-preview.png')
