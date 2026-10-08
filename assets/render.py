"""Render a seamless ASCII kinetic field. Run with Python and Pillow."""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import math
from pathlib import Path

COLS, ROWS = 216, 92
CW, CH = 6, 10
COUNT = 112
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 10)
# All marks are ASCII; their density and angle suggest flipping elements.
marks = ' .:-=+*#%@'
background = (13, 15, 17)
source = Image.open(Path(__file__).with_name('face.png')).convert('RGB')
portrait = source.resize((144, 86), Image.Resampling.LANCZOS)
# Preserve natural light/dark relationships; sharpen existing features.
gray = ImageOps.autocontrast(source.convert('L'), cutoff=1)
gray = gray.filter(ImageFilter.UnsharpMask(radius=1.1, percent=190, threshold=3))
gray = gray.resize((144, 86), Image.Resampling.LANCZOS)
portrait_values = {}
for py in range(86):
    for px in range(144):
        red, green, blue = portrait.getpixel((px, py))
        if min(red, green, blue) > 223:
            value = 0.0
        else:
            luminance = gray.getpixel((px, py))/255
            value = 0.10 + 0.88*luminance**0.85
        portrait_values[(px, py)] = value
# Keep the same palette throughout the loop to avoid brightness flicker.
palette_image = Image.new('P', (1, 1))
palette_image.putpalette(list(background) + [channel for v in range(1,256) for channel in (v,v,min(255,v+4))])
def sample_portrait(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x-ix, y-iy
    return sum(portrait_values.get((ix+dx,iy+dy),0)*wx*wy
               for dx,wx in ((0,1-fx),(1,fx))
               for dy,wy in ((0,1-fy),(1,fy)))
frames = []
for frame in range(COUNT):
    t = frame / COUNT * math.tau
    progress = frame / COUNT
    # Smooth reveal, a still portrait, and a smooth return to the waves.
    def smooth(v):
        v = max(0, min(1, v))
        return v*v*(3-2*v)
    reveal = smooth((progress-0.04)/0.28) * (1-smooth((progress-0.78)/0.22))
    # Enter and leave facing forward; rotate only while fully revealed.
    orbit = max(0,min(1,(progress-0.32)/0.46))
    turn_envelope = smooth(orbit/0.12)*smooth((1-orbit)/0.12)
    # An inferred shallow face relief: curved cheeks, brow, and nose.
    # Inverse projection avoids gaps as the textured surface turns.
    yaw = 0.72*math.sin(orbit*math.tau)*turn_envelope
    pitch = 0.16*math.sin(orbit*math.tau)*turn_envelope
    face_values = {}
    def relief(u, v):
        oval = max(0, 1-(u/68)**2-((v-2)/43)**2)
        nose = 13*math.exp(-(u/9)**2-((v-5)/12)**2)
        return 28*math.sqrt(oval)+nose
    for py in range(86):
        for px in range(160):
            screen_x, screen_y = px-80, py-43
            u, v = screen_x, screen_y
            for _ in range(3):
                depth = relief(u,v)
                u = (screen_x-(depth-14)*math.sin(yaw))/math.cos(yaw)
                v = screen_y+(depth-14)*math.sin(pitch)
            tone = sample_portrait(u+72,v+43)
            if tone:
                slope = (relief(u+1,v)-relief(u-1,v))/2
                shade = max(0.65,min(1.15,0.96+0.18*slope*math.sin(yaw+0.6)))
                face_values[(px+28,py+3)] = min(0.99,tone*shade)
    canvas = Image.new('RGB' , (COLS*CW, ROWS*CH), background)
    draw = ImageDraw.Draw(canvas)
    for row in range(ROWS):
        for col in range(COLS):
            x = (col-(COLS-1)/2)/46.5
            y = (row-(ROWS-1)/2)/35.3
            # Traveling folds with a slow twisting center and concentric wake.
            bend = 0.50*math.sin(x*1.5-t) + 0.20*math.cos(x*2+t)
            yy = y-bend
            radius = math.sqrt(x*x*0.58+yy*yy)
            a = math.atan2(yy,x)
            carrier = math.sin(yy*9 + 1.8*math.sin(x*2-t) + t*2)
            wake = math.cos(radius*10-t*2+0.8*math.sin(a*2+t))
            envelope = math.exp(-0.22*x*x-0.68*y*y)
            value = max(0,min(1,(0.5+0.34*carrier+0.16*wake)*envelope))
            # The wave field quiets as its characters settle into the face.
            # Residual flow gently bends the portrait, then reaches zero.
            drift = 4*(1-reveal)*math.sin(y*2-t)
            sample_x = col+drift
            left = math.floor(sample_x)
            frac = sample_x-left
            face = (face_values.get((left,row),0)*(1-frac)
                    + face_values.get((left+1,row),0)*frac)
            value = value*(1-reveal)**2 + face*reveal*(1+0.25*(1-reveal)*carrier)
            value = min(0.99,max(0,value))
            idx = min(len(marks)-1,int(value*len(marks)))
            char = marks[idx]
            if char == ' ': continue
            brightness = int(28+value*227)
            draw.text((col*CW,row*CH),char,font=font,fill=(brightness,brightness,min(255,brightness+4)))
    frames.append(canvas.quantize(palette=palette_image, dither=Image.Dither.NONE))
frames[0].save('assets/kinetic.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=2)
frames[56].convert('RGB').save('/tmp/z-face-preview.png')
frames[38].convert('RGB').save('/tmp/z-turn-preview.png')
frames[24].convert('RGB').save('/tmp/z-transition-preview.png')
