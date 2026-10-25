#!/usr/bin/env python3
"""Deterministic geometric message demo. No cryptographic secrecy/integrity."""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw

WHITE = (255, 255, 255)
HORIZON = 400
MAX_LETTERS = 40


def validate(text):
    if not re.fullmatch(r'[A-Z]+(?: [A-Z]+)*', text):
        raise ValueError('Use uppercase A-Z with single spaces only')
    if len(text.replace(' ', '')) > MAX_LETTERS:
        raise ValueError('Message exceeds 40 letters')
    return text


def encode(text, output):
    validate(text)
    positions = []
    x = 100
    for c in text:
        if c == ' ':
            x += 120
            continue
        positions.append((x, HORIZON - 10 * (ord(c) - 64)))
        x += 80
    width = max(1200, positions[-1][0] + 180)
    im = Image.new('RGB', (width, 800))
    d = ImageDraw.Draw(im)
    for y in range(800):
        if y < HORIZON:
            t = y / HORIZON
            color = (int(8 + 12*t), int(17 + 19*t), int(37 + 24*t))
        else:
            t = (y-HORIZON)/400
            color = (int(12-5*t), int(33-17*t), int(48-20*t))
        d.line((0, y, width-1, y), fill=color)
    d.polygon([(0,400),(0,340),(58,310),(130,355),(210,326),
               (300,370),(380,348),(470,386),(540,400)], fill=(19,36,51))
    d.polygon([(width-450,400),(width-350,365),(width-250,338),
               (width-170,360),(width-85,303),(width,344),(width,400)], fill=(19,36,51))
    d.line((0,400,width-1,400), fill=(86,117,133), width=2)
    d.ellipse((width-135,65,width-65,135), fill=(227,221,187))
    d.ellipse((width-151,54,width-81,124), fill=(12,23,45))
    for x,y in positions:
        d.polygon([(x,y-6),(x+2,y-2),(x+6,y),(x+2,y+2),
                   (x,y+6),(x-2,y+2),(x-6,y),(x-2,y-2)], fill=(255,244,196))
        d.point((x,y), fill=WHITE)
    for j in range(30):
        y=440+j*10; half=12+j*5; cx=width-105+int(8*math.sin(j))
        d.line((cx-half,y,cx+half,y), fill=(39,58,65))
    for j in range(22):
        y=455+j*14; x=(j*173)%(width-100)
        d.line((x,y,x+50+(j%5)*14,y), fill=(19,44,57))
    d.polygon([(0,800),(0,745),(150,722),(275,753),(410,743),(560,800)], fill=(5,15,24))
    # Exclusive creation prevents overwriting even with a racing producer.
    with Path(output).open('xb') as f:
        im.save(f, format='PNG')


def decode(source):
    with Image.open(source) as original:
        if original.format != 'PNG' or original.height != 800 or not 1200 <= original.width <= 8000:
            raise ValueError('Unsupported image format or dimensions')
        if original.width*original.height > 6400000:
            raise ValueError('Image too large')
        im=original.convert('RGB')
    if any(im.getpixel((x,400)) != (86,117,133) for x in range(im.width)):
        raise ValueError('Expected horizon not found')
    centers = [(x,y) for y in range(400) for x in range(im.width)
               if im.getpixel((x,y)) == WHITE]
    centers.sort()
    if not 1 <= len(centers) <= MAX_LETTERS or centers[0][0] != 100:
        raise ValueError('Invalid star pattern')
    result = ''
    for i,(x,y) in enumerate(centers):
        n, remainder = divmod(HORIZON-y, 10)
        if remainder or not 1 <= n <= 26:
            raise ValueError('Invalid letter geometry')
        if i:
            gap = x-centers[i-1][0]
            if gap not in (80,200):
                raise ValueError('Invalid star spacing')
            if gap == 200:
                result += ' '
        result += chr(64+n)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('encode');a.add_argument('--message-file',type=Path);a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('decode');a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.mode == 'encode':
            text=args.message_file.read_text() if args.message_file else sys.stdin.read()
            # Permit one conventional input terminator, no silent normalization.
            if text.endswith('\n'):
                text=text[:-1]
            encode(text,args.output)
        else:
            text=decode(args.input)
            fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w',encoding='utf8') as f:
                f.write(text+'\n')
        print(json.dumps({'status':'ok','operation':args.mode}))
        return 0
    except (OSError,ValueError,Image.DecompressionBombError):
        print(json.dumps({'status':'failed','reason':'invalid_input_or_output_unavailable'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
