import os
from PIL import Image, ImageDraw

os.makedirs('static/icons', exist_ok=True)

def create_icon(size, filename):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background
    radius = size // 4
    draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=(26, 35, 50, 255))

    # Outer green circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill=(46, 125, 50, 255))

    # Inner lighter circle
    m2 = size // 4
    draw.ellipse([m2, m2, size-m2, size-m2], fill=(76, 175, 80, 255))

    # Letter N in center
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("arialbd.ttf", size//3)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", size//3)
        except:
            font = ImageFont.load_default()

    text = "N"
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    img.save(filename, 'PNG')
    print('Created ' + filename)

create_icon(192, 'static/icons/icon-192.png')
create_icon(512, 'static/icons/icon-512.png')
print('Done!')