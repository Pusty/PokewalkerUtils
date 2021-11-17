from pokewalker_header import *


"""
0xCE80-0xCE87	unused
0xCE88	If low bit set, game will give player a STARF berry ONCE per savefile. Used when 99999 steps reached
0xCE89	unused
0xCE8A-0xCE8B	current watts written to eeprom by cmd 0x20 before replying (likely so remote can read them directly). u16 BE
0xCE8C-0xCEBB	3x route-available pokemon we've caught so far. 3x struct PokemonSummary
0xCEBC-0xCEC7	3x route-available items we've dowsed so far. 3x {u16 LE item, u16 LE unused}
0xCEC8-0xCEEF	10x route-available items we've been gifted by peer play. 3x {u16 LE item, u16 LE unused}
0xCEF0-0xCF0B	historic step count per day. u32 each, BE, [0] is yesterday, [1] is day before, etc...
"""


def catchPokemon(deviceMemory):
    routeInfo = RouteInfo()
    routeInfo.decode(deviceMemory[0x8F00:0x8FBD])
    writePokemon(deviceMemory, routeInfo.routePokes[0], 0)
    writePokemon(deviceMemory, routeInfo.routePokes[1], 1)
    writePokemon(deviceMemory, routeInfo.routePokes[2], 2)

def writePokemon(deviceMemory, pkmn, slot=0):
    offset = 0xCE8C+slot*16
    deviceMemory[offset:offset+16] = pkmn.encode()
    
def writeItem(deviceMemory, itemID, slot=0):
    offset = 0xCEBC+slot*4
    deviceMemory[offset] = int(itemID&0xFF)
    deviceMemory[offset+1] = int((itemID>>8)&0xFF)
    deviceMemory[offset+2] = 0
    deviceMemory[offset+3] = 0
    
def writeItemPeerPlay(deviceMemory, itemID, slot=0):
    offset = 0xCEC8+slot*4
    deviceMemory[offset] = int(itemID&0xFF)
    deviceMemory[offset+1] = int((itemID>>8)&0xFF)
    deviceMemory[offset+2] = 0
    deviceMemory[offset+3] = 0


def writeWatt(deviceMemory, watt):
    deviceMemory[0xCE8A] = ((watt>>8)&0xFF)
    deviceMemory[0xCE8B] = ((watt)&0xFF)
    
def writeSteps(deviceMemory, steps):
    id = IdentityData()
    id.decode(deviceMemory[0x00ED:0x0155])
    id.stepCount = steps
    deviceMemory[0x00ED:0x0155] = id.encode()

def writeStepHistory(deviceMemory, steps, dayoffset=0):
    offset = 0xCEF0+4*dayoffset
    deviceMemory[offset] = ((steps>>24)&0xFF)
    deviceMemory[offset+1] = ((steps>>16)&0xFF)
    deviceMemory[offset+2] = ((steps>>8)&0xFF)
    deviceMemory[offset+3] = ((steps)&0xFF)
    

#0x1A90 0xc0 32
def decodeImage(deviceMemory, offset, width, height):
    inputData = [0] * ((width * height) // 4)
    for i in range(len(inputData)):
        inputData[i] = (deviceMemory[offset+i*2] << 8) + deviceMemory[offset+i*2+1];
    decoded = [ 0 ] * (width * height)
    index = 0
    for r in range(0, height, 8):
        for c in range(width):
            for r2 in range(8):
                v = (inputData[index] >> r2) & 0x0101
                if v == 0x000: # white
                    decoded[(r+r2) * width + c] = 0x0
                elif v == 0x001: # dark grey
                    decoded[(r+r2) * width + c] = 0x1
                elif v == 0x100: # light grey
                    decoded[(r+r2) * width + c] = 0x2
                elif v == 0x101: # black
                    decoded[(r+r2) * width + c] = 0x3
            index = index + 1
            
    return decoded
    


if __name__ == "__main__":

    deviceMemory = [0]*0x10000
    f = open("eeprom.bin", "rb")
    d = f.read()
    for i in range(len(d)):
        deviceMemory[i] = d[i]
    f.close()
    
    catchPokemon(deviceMemory)
    writeWatt(deviceMemory, 5000)
    writeSteps(deviceMemory, 100)
    
    f = open("eeprom.bin", "wb")
    f.write(bytes(deviceMemory))
    f.close()
    
    
"""
    deviceMemory = [0]*0x10000
    f = open("eeprom_send.bin", "rb")
    d = f.read()
    for i in range(len(d)):
        deviceMemory[i] = ord(d[i])
    f.close()


    tD = deviceMemory[0xCC00:0xCC00+640]
    teamData = TeamData()
    teamData.decode(tD)
    print(teamData.pokes[0])
    print(teamData.pokes[1])
    print(teamData.pokes[2])
    print(teamData.pokes[3])
    print(teamData.pokes[4])
    print(teamData.pokes[5])


    rI = deviceMemory[0x8F00:0x8FBD]
    routeInfo = RouteInfo()
    routeInfo.decode(rI)
    print(routeInfo.routePokes[2])
    
"""
    
"""
for i in range(10):
    eL = deviceMemory[0xCF0C+136*i:0xCF0C+136*i+136]
    eventLog = EventLogItem()
    eventLog.decode(eL)
    print(eL)
"""