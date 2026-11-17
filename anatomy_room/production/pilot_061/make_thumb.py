from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
im = Image.open('work/blender/s01/f_0222.png').convert('RGB').resize((1080,1920), Image.LANCZOS)
# 上下を少し暗く
sh = Image.new('L', (1080,1920), 0); d = ImageDraw.Draw(sh)
for y in range(1920):
    a = max(0, 150 - y*0.35) if y < 520 else max(0, (y-1350)*0.3)
    d.line([(0,y),(1080,y)], fill=int(min(170,a)))
im = Image.composite(Image.new('RGB',(1080,1920),(10,6,3)), im, sh)
F = ImageFont.truetype('assets/fonts/ShipporiMinchoB1-ExtraBold.ttf', 136)
def gold_text(s, cy):
    d = ImageDraw.Draw(im); w = d.textlength(s, font=F); x = 540 - w/2
    d.text((x, cy), s, font=F, anchor='lm', fill=(26,10,4), stroke_width=16, stroke_fill=(26,10,4))
    mask = Image.new('L', im.size, 0); ImageDraw.Draw(mask).text((x, cy), s, font=F, anchor='lm', fill=255)
    grad = Image.new('RGB', im.size); gd = ImageDraw.Draw(grad)
    for y in range(int(cy-70), int(cy+70)):
        t = (y-(cy-70))/140; gd.line([(0,y),(1080,y)], fill=(int(255-(255-192)*t), int(240-(240-122)*t), int(168-(168-24)*t)))
    im.paste(grad, (0,0), mask)
gold_text('お金が全部', 230); gold_text('金になったら？', 390)
d = ImageDraw.Draw(im)
d.rounded_rectangle([170,1560,910,1740], 24, fill=(200,30,30))
d.text((540,1650), '金が4.8倍足りない', font=ImageFont.truetype('assets/fonts/BIZUDPGothic-Bold.ttf', 80), anchor='mm', fill='white')
im.save('thumbnail.png')
