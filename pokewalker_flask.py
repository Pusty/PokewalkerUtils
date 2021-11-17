from pokewalker_header import *
from pokewalker_eeprom import *

from flask import send_file, Flask, Response
from PIL import Image
import io
import base64


app = Flask(__name__, static_url_path='', static_folder='html')
app.config.from_object(__name__)


deviceMemory = [0]*0x10000
f = open("eeprom.bin", "rb")
d = f.read()
for i in range(len(d)):
    deviceMemory[i] = d[i]
f.close()


def createImage(deviceMemory, offset, width, height):
    img = Image.new('P', (width, height))
    decoded = decodeImage(deviceMemory, offset, width, height)
    img.putdata(decoded)
    img.putpalette([255,255,255,180,180,180,70,70,70, 0,0,0])
    return img

def drawImage(deviceMemory, offset, width, height, show=False):
    img =  createImage(deviceMemory, offset, width, height)
    if show:
        img.show() 
    data = io.BytesIO()
    img.save(data, "PNG")
    data.seek(0)
    return (data, 'image/png')
    
def drawGIF(deviceMemory, offset, width, height, frames):
    imgs = []
    for f in range(frames):
        imgs.append(createImage(deviceMemory, offset+(f*((width*height)//4)), width, height))
        
    data = io.BytesIO()
    imgs[0].save(data, "GIF", save_all=True, append_images=imgs[1:], duration=600, loop=0, include_color_table=True, interlace=False)
    data.seek(0)
    
    return (data, 'image/gif')
    
    
@app.route('/')
def root():
    return app.send_static_file('index.html')
    

pngMap = {
    
    "0": (0x0280, 8, 16),
    "1": (0x0280+32, 8, 16),
    "2": (0x0280+32*2, 8, 16),
    "3": (0x0280+32*3, 8, 16),
    "4": (0x0280+32*4, 8, 16),
    "5": (0x0280+32*5, 8, 16),
    "6": (0x0280+32*6, 8, 16),
    "7": (0x0280+32*7, 8, 16),
    "8": (0x0280+32*8, 8, 16),
    "9": (0x0280+32*9, 8, 16),
    "10": (0x0280+32*10, 8, 16),
    "11": (0x0280+32*11, 8, 16),
    "12": (0x0280+32*12, 8, 16),

    "box": (0x1A90, 32, 24),
    "pokemon_name": ( 0x993E, 80, 16),
    "route_pokemon0_name": (0xA4FE, 80, 16),
    "route_pokemon1_name": (0xA63E, 80, 16),
    "route_pokemon2_name": (0xA77E, 80, 16),
    "route_item0_name": (0xA8BE, 96, 16),
    "route_item1_name": (0xA8BE+0x180, 96, 16),
    "route_item2_name": (0xA8BE+0x180*2, 96, 16),
    "route_item3_name": (0xA8BE+0x180*3, 96, 16),
    "route_item4_name": (0xA8BE+0x180*4, 96, 16),
    "route_item5_name": (0xA8BE+0x180*5, 96, 16),
    "route_item6_name": (0xA8BE+0x180*6, 96, 16),
    "route_item7_name": (0xA8BE+0x180*7, 96, 16),
    "route_item8_name": (0xA8BE+0x180*8, 96, 16),
    "route_item9_name": (0xA8BE+0x180*9, 96, 16),
    "route_img": (0x8FBE, 32, 24),
    "route_name": (0x907E, 80, 16),
    
    
    "watt_symbol": (0x0420, 16,16),
    "pokeball_8x8": (0x0460, 8, 8),
    "pokeball_8x8_light": (0x0470, 8, 8),
    "item_8x8": (0x0488, 8, 8),
    "item_8x8_light": (0x0498, 8, 8),
    "map_8x8": (0x04A8, 8, 8),
    
    "stamp_8x8_heart": (0x04B8, 8, 8),
    "stamp_8x8_spade": (0x04C8, 8, 8),
    "stamp_8x8_diamond": (0x04D8, 8, 8),
    "stamp_8x8_club": (0x04E8, 8, 8),
    
    "arrow_8x8_up": (0x04F8, 8, 8),
    "arrow_8x8_up_offset": (0x0508, 8, 8),
    "arrow_8x8_up_inverted": (0x0518, 8, 8),
    "arrow_8x8_down": (0x0528, 8, 8),
    "arrow_8x8_down_offset": (0x0538, 8, 8),
    "arrow_8x8_down_inverted": (0x0548, 8, 8),
    "arrow_8x8_left": (0x0558, 8, 8),
    "arrow_8x8_left_offset": (0x0568, 8, 8),
    "arrow_8x8_left_inverted": (0x0578, 8, 8),
    "arrow_8x8_right": (0x0588, 8, 8),
    "arrow_8x8_right_offset": (0x0598, 8, 8),
    "arrow_8x8_right_inverted": (0x05A8, 8, 8),
    
    "arrow_left": (0x05B8, 8, 16),
    "arrow_right": (0x05D8, 8, 16),
    "arrow_return": (0x05F8, 8, 16),
    
    "gift_8x8": (0x0650, 8, 8),
    "battery_8x8": (0x0660, 8, 8),
    
    "bubble_exclamation": (0x0670, 24, 16),
    "bubble_heart": (0x0670+0x60, 24, 16),
    "bubble_music": (0x0670+0x60*2, 24, 16),
    "bubble_smile": (0x0670+0x60*3, 24, 16),
    "bubble_neutral": (0x0670+0x60*4, 24, 16),
    "bubble_ellipsis": (0x0670+0x60*5, 24, 16),
    "bubble_exclamation2": (0x0670+0x60*6, 24, 16),
    
    "menu_radar": (0x0910, 80, 16),
    "menu_dowsing": (0x0A50, 80, 16),
    "menu_connect": (0x0B90, 80, 16),
    "menu_card": (0x0CD0, 80, 16),
    "menu_pkmn": (0x0E10, 80, 16),
    "menu_settings": (0x0F50, 80, 16),
    
    "icon_radar": (0x1090, 16, 16),
    "icon_dowsing": (0x10D0, 16, 16),
    "icon_connect": (0x1110, 16, 16),
    "icon_card": (0x1150, 16, 16),
    "icon_pkmn": (0x1190, 16, 16),
    "icon_settings": (0x11D0, 16, 16),
    
    "card_person": (0x1210, 16, 16),
    "card_name": (0x1250, 80, 16),
    "card_route": (0x1390, 16, 16),
    "card_steps": (0x13D0, 40, 16),
    "card_time": (0x1470, 32, 16),
    "card_days": (0x14F0, 40, 16),
    "card_total": (0x1590, 64, 16),
    "settings_sound": (0x1690, 40, 16),
    "settings_shade": (0x1730, 40, 16),
    "settings_sound_off": (0x17D0, 24, 16),
    "settings_sound_low": (0x1830, 24, 16),
    "settings_sound_high": (0x1890, 24, 16),
    
    
    "items_tresure": (0x1910, 32, 24),
    "items_scoll": (0x19D0, 32, 24),
    "items_present": (0x1A90, 32, 24),
    
    
    "dowsing_bush": (0x1B50, 16, 16),
    "dowsing_bush_light": (0x1B90, 16, 16),
    
    "dowsing_left": (0x1BD0, 32, 16),
    
    "radar_bush": (0x1CB0, 32, 24),
    "radar_exclamation0": (0x1D70, 16, 16),
    "radar_exclamation1": (0x1DB0, 16, 16),
    "radar_exclamation2": (0x1DF0, 16, 16),
    "radar_click" : (0x1E30, 16, 16),
    
    
    "battle_attack": (0x1E70, 16, 32),
    "battle_attack_crit": (0x1EF0, 16, 32),
    "battle_appeared": (0x1F70, 32, 24),
    "battle_hp": (0x2030, 8, 8),
    "battle_catch": (0x2040, 8, 8),
    "battle_menu": (0x2050, 96, 32),
    
    
    # lots of text - adding when needed
    "text_discover" : (0x47B0, 96, 16),
    
}


gifMap = {
    "pokemon": (0x91BE, 32, 24, 2),
    "pokemon_big": (0x933E, 64 , 48, 2),
    "route_pokemon0": (0x9A7E, 32, 24, 2),
    "route_pokemon1": (0x9BFE, 32, 24, 2),
    "route_pokemon2": (0x9D7E, 32, 24, 2),
    "route_pokemon_big": (0x9EFE, 64, 48, 2),
    
}
    
@app.route('/img/<path:path>.png')
def dynamicImage(path):
    if not (path in pngMap): return ""
    return send_file(*drawImage(deviceMemory, *pngMap[path]))
    
@app.route('/img/<path:path>.gif')
def dynamicImageGIF(path):
    if not (path in gifMap): return ""
    return send_file(*drawGIF(deviceMemory, *gifMap[path]))
    

if __name__ == '__main__':  # pragma: no cover
    app.run(port=8080)
    


