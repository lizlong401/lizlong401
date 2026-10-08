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
frames = []
for frame in range(COUNT):
    t = frame / COUNT * math.tau
    # An inferred shallow face relief: curved cheeks, brow, and nose.
    # Inverse projection avoids gaps as the textured surface turns.
    yaw = 0.72*math.sin(t)
    pitch = 0.22*math.cos(t)
    # Background displacement uses the same pose vector as the head.
    # No independent wave clock: both layers reverse direction together.
    flow_x = 0.85*math.sin(yaw)
    flow_y = -0.90*math.sin(pitch)
    flow_angle = 0.24*yaw + 0.35*pitch
    flow_cos, flow_sin = math.cos(flow_angle), math.sin(flow_angle)
    flow_phase = 0.60*yaw - 0.40*pitch
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
            sx, sy = int(round(u+72)), int(round(v+43))
            tone = portrait_values.get((sx,sy),0)
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
            # Move, tilt, and compress the field with the turning head.
            dx,dy = x-flow_x,y-flow_y
            wx = (dx*flow_cos+dy*flow_sin)/math.cos(yaw)
            wy = -dx*flow_sin+dy*flow_cos
            bend = 0.50*math.sin(wx*1.5-flow_phase) + 0.20*math.cos(wx*2+flow_phase)
            yy = wy-bend
            radius = math.sqrt(wx*wx*0.58+yy*yy)
            a = math.atan2(yy,wx)
            carrier = math.sin(yy*9 + 1.8*math.sin(wx*2-flow_phase) + flow_phase*2)
            wake = math.cos(radius*10-flow_phase*2+0.8*math.sin(a*2+flow_phase))
            envelope = math.exp(-0.22*wx*wx-0.68*wy*wy)
            value = max(0,min(1,(0.5+0.34*carrier+0.16*wake)*envelope))
            # Opaque portrait in front; waves stay behind the silhouette.
            if (col,row) in face_values:
                value = face_values[(col,row)]
            else:
                value *= 0.65
            idx = min(len(marks)-1,int(value*len(marks)))
            char = marks[idx]
            if char == ' ': continue
            brightness = int(28+value*227)
            draw.text((col*CW,row*CH),char,font=font,fill=(brightness,brightness,min(255,brightness+4)))
    frames.append(canvas.quantize(colors=64))
frames[0].save('assets/kinetic.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=2)
frames[0].convert('RGB').save('/tmp/z-face-preview.png')
frames[38].convert('RGB').save('/tmp/z-turn-preview.png')
