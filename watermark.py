import os
import sys
from datetime import datetime
now = datetime.now().isoformat(' ', 'seconds')

from PIL import Image

def resize_logo(logo_path, divisor):
    try:
        logo = Image.open(logo_path) # logo path

        # resize
        logo = logo.resize(((logo.width//divisor), (logo.height//divisor)))

        return logo

    except Exception as e:
        print(e)


def apply_watermark(pos, logo_path, img_path):

    print(f"{now} Applying watermark...")

    logo = resize_logo(logo_path, 2)
    logoWidth = logo.width
    logoHeight = logo.height

    image = Image.open(str(img_path))
    imageWidth = image.width
    imageHeight = image.height

    try:
        if pos == 'topleft':
            image.paste(logo, (0, 0), logo)
        elif pos == 'topright':
            image.paste(logo, (imageWidth - logoWidth, 0), logo)
        elif pos == 'bottomleft':
            image.paste(logo, (0, imageHeight - logoHeight), logo)
        elif pos == 'bottomright':
            image.paste(logo, (imageWidth - logoWidth, imageHeight - logoHeight), logo)
        elif pos == 'center':
            image.paste(logo, ((imageWidth - logoWidth)/2, (imageHeight - logoHeight)/2), logo)
        else:
            print('Error: ' + pos + ' is not a valid position')

        image.save(str(img_path))
        #print('Added watermark to ' + str(img_path))

    except Exception as e:
        print(e)
        image.paste(logo, ((imageWidth - logoWidth)/2, (imageHeight - logoHeight)/2), logo)
        image.save(img_path)
        #print('Added default watermark to ' + str(img_path))



