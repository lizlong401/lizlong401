"""Render a seamless ASCII kinetic field. Run with Python and Pillow."""
from PIL import Image, ImageDraw, ImageFont
import math
from pathlib import Path

COLS, ROWS = 144, 60
CW, CH = 8, 13
COUNT = 112
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 12)
# All marks are ASCII; their density and angle suggest flipping elements.
marks = ' .:-=+*#%@'
background = (13, 15, 17)
portrait = Image.open(Path(__file__).with_name('face.png')).convert('RGB').resize((84, 56), Image.Resampling.LANCZOS)
face_values = {}
for py in range(56):
    for px in range(84):
        red, green, blue = portrait.getpixel((px, py))
        if min(red, green, blue) > 223:
            value = 0.0
        else:
            luminance = (0.2126*red + 0.7152*green + 0.0722*blue)/255
            value = 0.18 + 0.80*(1-luminance)
        face_values[(px+30, py+2)] = value
frames = []
for frame in range(COUNT):
    t = frame / COUNT * math.tau
    progress = frame / COUNT
    # Smooth reveal, a still portrait, and a smooth return to the waves.
    def smooth(v):
        v = max(0, min(1, v))
        return v*v*(3-2*v)
    reveal = smooth((progress-0.12)/0.20) * (1-smooth((progress-0.68)/0.20))
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
            face = face_values.get((col,row), 0.0)
            value = value*(1-reveal) + face*reveal
            idx = min(len(marks)-1,int(value*len(marks)))
            char = marks[idx]
            if char == ' ': continue
            brightness = int(65+value*184)
            draw.text((col*CW,row*CH),char,font=font,fill=(brightness,brightness,min(255,brightness+4)))
    frames.append(canvas.quantize(colors=32))
frames[0].save('assets/kinetic.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=2)
frames[56].convert('RGB').save('/tmp/z-face-preview.png')
