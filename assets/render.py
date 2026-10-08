"""Render an inferred 3D head as a seamless ASCII turntable using Pillow.
The supplied photograph textures the front; sides/back are approximations.
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from pathlib import Path
import math

COLS, ROWS = 180, 100
CW, CH = 7, 11
COUNT, DELAY = 100, 80
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
marks = ' .,:;irsXAHM#@'
background = (12, 14, 17)
original = Image.open(Path(__file__).with_name('face.png')).convert('RGB')
source = original.convert('L')
source = ImageOps.autocontrast(source, cutoff=1).filter(ImageFilter.UnsharpMask(radius=1,percent=150,threshold=3))
texture = source.load()
tw, th = source.size
palette = Image.new('P',(1,1))
palette.putpalette(list(background)+[c for v in range(1,256) for c in (v,v,min(255,v+4))])

# Ellipsoid components in head space: cranium, nose, and both ears.
parts = [
    ((0,0,0),(.73,1,.65),'head'),
    ((0,-.12,.64),(.105,.18,.17),'nose'),
    ((-.73,-.035,-.015),(.115,.235,.10),'ear'),
    ((.73,-.035,-.015),(.115,.235,.10),'ear'),
]
def intersect(origin, direction, center, radii):
    o = tuple((origin[i]-center[i])/radii[i] for i in range(3))
    d = tuple(direction[i]/radii[i] for i in range(3))
    a = sum(v*v for v in d)
    b = 2*sum(o[i]*d[i] for i in range(3))
    c = sum(v*v for v in o)-1
    disc = b*b-4*a*c
    if disc < 0: return None
    return (-b-math.sqrt(disc))/(2*a)
def sample(u,v):
    x = max(0,min(tw-1.001,u*(tw-1)))
    y = max(0,min(th-1.001,v*(th-1)))
    ix,iy = int(x),int(y)
    fx,fy = x-ix,y-iy
    return sum(texture[ix+dx,iy+dy]*wx*wy for dx,wx in ((0,1-fx),(1,fx)) for dy,wy in ((0,1-fy),(1,fy)))/255

def render(frame):
    # Start facing forward, then turn through the entire head.
    angle = frame/COUNT*math.tau
    co,si = math.cos(angle),math.sin(angle)
    direction = (si,0,-co)
    image = Image.new('RGB',(COLS*CW,ROWS*CH),background)
    draw = ImageDraw.Draw(image)
    for row in range(ROWS):
        y = (49.5-row)/43
        for col in range(COLS):
            x = (col-89.5)/(43*CH/CW)
            if abs(x)>.93 or abs(y)>1.02: continue
            origin = (co*x-si*3,y,si*x+co*3)
            hit = None
            for center,radii,kind in parts:
                dist = intersect(origin,direction,center,radii)
                if dist is not None and (hit is None or dist<hit[0]):
                    hit = (dist,center,radii,kind)
            if hit is None: continue
            dist,center,radii,kind = hit
            p = tuple(origin[i]+dist*direction[i] for i in range(3))
            normal = tuple((p[i]-center[i])/radii[i]**2 for i in range(3))
            length = math.sqrt(sum(v*v for v in normal))
            nx,ny,nz = (v/length for v in normal)
            # Transform the surface normal into camera space.
            cx,cz = co*nx+si*nz,-si*nx+co*nz
            light = max(0,-.40*cx+.35*ny+.84*cz)
            rim = (1-max(0,cz))**3
            longitude = math.atan2(p[0]/.73,p[2]/.65)
            front = max(0,min(1,(1.28-abs(longitude))/.40))
            hair = p[1]>.48 or (abs(longitude)>1.22 and p[1]>-.65)
            base = .115 if hair else .51
            if hair:
                base += .035*math.sin(longitude*47+p[1]*22)
            if kind == 'head' and front>0:
                # Map the original frontal head photo onto the curved surface.
                u,v = (p[0]/.73+1)/2,(1-p[1])/2
                photo = sample(u,v)
                pixel = original.getpixel((max(0,min(tw-1,int(u*(tw-1)))),max(0,min(th-1,int(v*(th-1))))))
                photo = base if min(pixel)>223 else .09+.84*photo**.85
                base = base*(1-front)+photo*front
            elif kind == 'nose':
                base = .09+.84*sample((p[0]/.73+1)/2,(1-p[1])/2)**.85
            elif kind == 'ear':
                base = .38+.10*light
            tone = max(.035,min(.98,base*(.45+.68*light)+.10*rim))
            glyph = marks[min(len(marks)-1,int(tone*len(marks)))]
            brightness = int(45+210*tone)
            draw.text((col*CW,row*CH),glyph,font=font,fill=(brightness,brightness,min(255,brightness+4)))
    return image

frames = [render(frame).quantize(palette=palette,dither=Image.Dither.NONE) for frame in range(COUNT)]
frames[0].save('assets/kinetic.gif',save_all=True,append_images=frames[1:],duration=DELAY,loop=0,optimize=True,disposal=2)
for i,label in [(0,'front'),(20,'side'),(50,'back')]:
    frames[i].convert('RGB').save(f'/tmp/z-head-{label}.png')
