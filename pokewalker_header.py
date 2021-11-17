POKEWALKER_DATA_MAX_LEN = 128		#data per packet max, else we overflow pokewalker's buffer
POKEWALKER_CRC_START    = 0x0002
POKEWALKER_KEY          = 0xAA

DETAIL_DIR_TO_WALKER    = 0x01
DETAIL_DIR_FROM_WALKER  = 0x02


CMD_POKEWALKER_ADV      = 0xfc
CMD_POKEWALKER_SYN      = 0xfa
CMD_POKEWALKER_SYNACK   = 0xf8
CMD_POKEWALKER_DIS_REQ  = 0x66
CMD_POKEWALKER_DIS_RSP  = 0x68


CMD_EEPROM_READ_REQ     = 0x0c
CMD_EEPROM_READ_RSP     = 0x0e
CMD_EEPROM_WRITE_REQ    = 0x0a
CMD_EEPROM_WRITE_RSP    = 0x04
CMD_EVENT_POKE_RXED     = 0xc2
CMD_EVENT_ITEM_RXED     = 0xc4
CMD_EVENT_ROUTE_RXED    = 0xc6
CMD_WRITE               = 0x06


CMD_IDENTITY_DATA_REQ   = 0x20
CMD_IDENTITY_DATA_RSP   = 0x22
CMD_UNIQUE_ID_RESET     = 0x2A
CMD_IDENTITY_DATA_SEND       = 0x32
CMD_IDENTITY_DATA_SEND_RSP   = 0x34
CMD_IDENTITY_DATA_SEND2       = 0x40
CMD_IDENTITY_DATA_SEND_RSP2   = 0x42
CMD_IDENTITY_DATA_SEND3       = 0x60
CMD_IDENTITY_DATA_SEND_RSP3   = 0x62
CMD_IDENTITY_DATA_SEND4       = 0x52
CMD_IDENTITY_DATA_SEND_RSP4   = 0x54
CMD_EEPROM_WRITE_COMPRESSED_REQ = 0x80
CMD_EEPROM_WRITE_COMPRESSED_REQ2 = 0x00
CMD_EEPROM_WRITE_REQ2 = 0x02
CMD_EEPROM_WRITE_REQ3 = 0x82

CMD_PING = 0x24
CMD_PONG = 0x26

CMD_START_WALK = 0x38
CMD_START_WALK2 = 0x5A

CMD_END_WALK = 0x4E
CMD_END_WALK_RSP = 0x50

CMD_ERROR_CONNECTION = 0x64
CMD_COMPLETED_CONNECTION = 0x66
CMD_COMPLETED_CONNECTION_RSP = 0x68
CMD_ERROR_CONNECTION2 = 0x44
CMD_ERROR_CONNECTION3 = 0x36

CMD_DISCONNECT          = 0xF4


MODE_NORMAL = 0
MODE_DEBUG  = 1


def crcAlgorithm(data, v2):
    for i in range(len(data)):
        v4 = data[i]
        if (i&1) != 0:
            v2 += v4
        else:
            v2 += v4 << 8
            
    while ((v2 >> 16) != 0):
        v2 = (v2&0xFFFF) + ((v2>>16)&0xFFFF);
    return v2&0xFFFF
    
def LZ77_decompress(input):
    # Each packet begins with a byte-sized header, followed by 8 chunks. 
    
    typeDec = input[0]
    sizeDec = input[1] | (input[2]<<8) | (input[3]<<16)
    
    currentIndex = 4
    data = []
    
    while currentIndex < len(input):
        if len(data) == sizeDec: break
        header = input[currentIndex]
        currentIndex = currentIndex + 1
        for packet in range(8):
            if len(data) == sizeDec: break
            if ((header<<packet) & 0x80) == 0:
                #print(str(currentIndex)+"/"+str(len(input))+" - "+str(packet)+" - "+str(len(data)))
                data.append(input[currentIndex])
                currentIndex = currentIndex + 1
            else:
                backReference = ((input[currentIndex]&0x0f) << 8) | (input[currentIndex+1])
                backReference = backReference + 1
                size = ((input[currentIndex]&0xf0)>>4)+3
                #print(backReference, size, [input[currentIndex], input[currentIndex+1]], currentIndex)
                offset = len(data)-backReference
                for i in range(size):
                    data.append(data[offset+i])
                currentIndex = currentIndex + 2
        #print(str(len(data))+"/"+str(sizeDec))
                
    assert(len(data) == sizeDec)
    return data
    
    
class PokePacket:
    def __init__(self):
        self.cmd = 0
        self.detail = 0
        self.crc = 0
        self.session = 0
    
    def decode(self, byteList):
        self.cmd = byteList[0]
        self.detail = byteList[1]
        self.crc = byteList[2] + (byteList[3]<<8)
        self.session = (byteList[4] + (byteList[5]<<8) + (byteList[6]<<16) + (byteList[7]<<24))
        
    def encode(self):
        return [self.cmd&0xFF, self.detail&0xFF, self.crc&0xFF, (self.crc>>8)&0xFF, int(self.session&0xFF), int((self.session>>8)&0xFF), int((self.session>>16)&0xFF), int((self.session>>24)&0xFF)]
  
    def calcCRC(self):
        data = self.encode()
        data[2] = 0
        data[3] = 0
        return crcAlgorithm(data, POKEWALKER_CRC_START)
        
    def size(self):
        return len(self.encode())
  

class UniqueIdentityData:
    def __init__(self): 
        self.data = [0] * 0x28
        
    def encode(self):
        return [int(d&0xFF) for d in self.data]
        
    def decode(self, byteList):
        self.data = byteList[:0x28]
        
    def size(self):
        return len(self.encode())
        
class EventBitmap:
    def __init__(self): 
        self.bitmap = [0] * 0x10
        
    def decode(self, byteList):
        self.bitmap = byteList[:0x10]
        
    def encode(self):
        return [int(d&0xFF) for d in self.bitmap]
        
    def size(self):
        return len(self.encode())

class IdentityData:
    def __init__(self):
        self.unk_0 = 1
        self.unk_1 = 0
        self.unk_2 = 1
        self.unk_3 = 1
        self.trainerTID = 0
        self.trainerSID = 0
        self.uniq = UniqueIdentityData()
        self.evtBmp = EventBitmap()
        self.trainerName = [0]*8
        self.unk_4 = 0
        self.unk_5 = 0
        self.unk_6 = 0
        self.flags = 0
        self.protoVer = 0
        self.unk_7 = 0
        self.protoSubver = 0
        self.unk_8 = 0
        self.lastSyncTime = 0
        self.stepCount = 0
        
    def decode(self, byteList):
        self.unk_0 = byteList[0] + (byteList[1] << 8) + (byteList[2] << 16) + (byteList[3] << 24)
        self.unk_1 = byteList[4] + (byteList[5] << 8) + (byteList[6] << 16) + (byteList[7] << 24)
        self.unk_2 = byteList[8] + (byteList[9] << 8)
        self.unk_3 = byteList[10] + (byteList[11] << 8)
        self.trainerTID = byteList[12] + (byteList[13] << 8)
        self.trainerSID = byteList[14] + (byteList[15] << 8)
        self.uniq.decode(byteList[16:56])
        self.evtBmp.decode(byteList[56:72])
        self.trainerName = [(byteList[72] + (byteList[73]<<8)), (byteList[74] + (byteList[75]<<8)), (byteList[76] + (byteList[77]<<8)) , (byteList[78] + (byteList[79]<<8)),
                            (byteList[80] + (byteList[81]<<8)), (byteList[82] + (byteList[83]<<8)), (byteList[84] + (byteList[85]<<8)) , (byteList[86] + (byteList[87]<<8))]
        self.unk_4 = byteList[88]
        self.unk_5 = byteList[89]
        self.unk_6 = byteList[90]
        self.flags = byteList[91]
        self.protoVer = byteList[92]
        self.unk_7 = byteList[93]
        self.protoSubver = byteList[94]
        self.unk_8 = byteList[95]
        self.lastSyncTime = byteList[99] + (byteList[98] << 8) + (byteList[97] << 16) + (byteList[96] << 24)
        self.stepCount = byteList[103] + (byteList[102] << 8) + (byteList[101] << 16) + (byteList[100] << 24)
        
    def encode(self):
        return [int(self.unk_0&0xFF),int((self.unk_0 >> 8)&0xFF),int((self.unk_0 >> 16)&0xFF),int((self.unk_0 >> 24)&0xFF),
                int(self.unk_1&0xFF),int((self.unk_1 >> 8)&0xFF),int((self.unk_1 >> 16)&0xFF),int((self.unk_1 >> 24)&0xFF),
                int(self.unk_2&0xFF),int((self.unk_2 >> 8)&0xFF),int(self.unk_3&0xFF),int((self.unk_3 >> 8)&0xFF),
                int(self.trainerTID&0xFF),int((self.trainerTID >> 8)&0xFF),int(self.trainerSID&0xFF),int((self.trainerSID >> 8)&0xFF)] + self.uniq.encode() + self.evtBmp.encode() + sum([[int(self.trainerName[i]&0xFF),int((self.trainerName[i] >> 8)&0xFF)] for i in range(8)], []) + [
                    int(self.unk_4&0xFF),int(self.unk_5&0xFF),int(self.unk_6&0xFF),int(self.flags&0xFF),int(self.protoVer&0xFF),int(self.unk_7&0xFF),int(self.protoSubver&0xFF),int(self.unk_8&0xFF),
                    int((self.lastSyncTime >> 24)&0xFF),int((self.lastSyncTime >> 16)&0xFF),int((self.lastSyncTime >> 8)&0xFF), int(self.lastSyncTime&0xFF),
                    int((self.stepCount >> 24)&0xFF),int((self.stepCount >> 16)&0xFF),int((self.stepCount >> 8)&0xFF), int(self.stepCount&0xFF)
                ]
        
    def size(self):
        return len(self.encode())
     

class TeamPokeData:
    def __init__(self):
        self.species = 0
        self.itemHeld = 0
        self.moves = [0]*4
        self.otTid = 0
        self.otSid = 0
        self.pid = 0
        self.IVs = 0 # 5 bits each, LSB to MSB: hp, atk, def, speed, spAtk, spDef
        self.EVs = [0]*6  # hp, atk, def, speed, spAtk, spDef
        self.variant = 0
        self.sourceGame = 0
        self.ability = 0
        self.happiness = 0
        self.level = 0
        self.padding = 0
        self.nickname = [0]*10
        
    def decode(self, byteList):
        self.species = byteList[0] + (byteList[1] << 8)
        self.itemHeld = byteList[2] + (byteList[3] << 8)
        self.moves[0] = byteList[4] + (byteList[5] << 8)
        self.moves[1] = byteList[6] + (byteList[7] << 8)
        self.moves[2] = byteList[8] + (byteList[9] << 8)
        self.moves[3] = byteList[10] + (byteList[11] << 8)
        self.otTid = byteList[12] + (byteList[13] << 8)
        self.otSid = byteList[14] + (byteList[15] << 8)
        self.pid = byteList[16] + (byteList[17] << 8) + (byteList[18] << 16) + (byteList[19] << 24)
        self.IVs = byteList[20] + (byteList[21] << 8) + (byteList[22] << 16) + (byteList[23] << 24)
        self.EVs = byteList[24:30]
        self.variant = byteList[30]
        self.sourceGame = byteList[31]
        self.ability = byteList[32]
        self.happiness = byteList[33]
        self.level = byteList[34]
        self.padding = byteList[35]
        self.nickname = [(byteList[36] + (byteList[37]<<8)), (byteList[38] + (byteList[39]<<8)), (byteList[40] + (byteList[41]<<8)) , (byteList[42] + (byteList[43]<<8)),
                         (byteList[44] + (byteList[45]<<8)), (byteList[46] + (byteList[47]<<8)), (byteList[48] + (byteList[49]<<8)) , (byteList[50] + (byteList[51]<<8)),
                         (byteList[52] + (byteList[53]<<8)), (byteList[54] + (byteList[55]<<8))]
        
    def encode(self):
        return [int(self.species&0xFF),int((self.species >> 8)&0xFF), int(self.itemHeld&0xFF),int((self.itemHeld >> 8)&0xFF), int(self.moves[0]&0xFF),int((self.moves[0] >> 8)&0xFF), int(self.moves[1]&0xFF),int((self.moves[1] >> 8)&0xFF), int(self.moves[2]&0xFF),int((self.moves[2] >> 8)&0xFF), int(self.moves[3]&0xFF),int((self.moves[3] >> 8)&0xFF),
                int(self.otTid&0xFF),int((self.otTid >> 8)&0xFF),int(self.otSid&0xFF),int((self.otSid >> 8)&0xFF),int(self.pid&0xFF),int((self.pid >> 8)&0xFF),int((self.pid >> 16)&0xFF),int((self.pid >> 24)&0xFF),
                int(self.IVs&0xFF),int((self.IVs >> 8)&0xFF),int((self.IVs >> 16)&0xFF),int((self.IVs >> 24)&0xFF),
                int(self.EVs[0]&0xFF),int(self.EVs[1]&0xFF),int(self.EVs[2]&0xFF),int(self.EVs[3]&0xFF),int(self.EVs[4]&0xFF),int(self.EVs[5]&0xFF),int(self.variant&0xFF),int(self.sourceGame&0xFF),
                int(self.ability&0xFF),int(self.happiness&0xFF),int(self.level&0xFF),int(self.padding&0xFF)]+ sum([[int(self.nickname[i]&0xFF),int((self.nickname[i] >> 8)&0xFF)] for i in range(10)], [])
                
    def size(self):
        return len(self.encode())
        
    def __str__(self):
        return "TeamPokeData(Type: "+str(self.species)+", LVL: "+str(self.level)+ ", Name: "+str(self.nickname)+")"


class TeamDataUnk:
    def __init__(self):
        self.flags = 0
        self.val = 0
        self.always_ffff = 0xffff
        
    def decode(self, byteList):
        self.flags = byteList[0] + (byteList[1] << 8) + (byteList[2] << 16) + (byteList[3] << 24)
        self.val = byteList[4] + (byteList[5] << 8)
        self.always_ffff = byteList[6] + (byteList[7] << 8)
        
        
    def encode(self):
        return [int(self.flags&0xFF),int((self.flags >> 8)&0xFF),int((self.flags >> 16)&0xFF),int((self.flags >> 24)&0xFF),
                int(self.val&0xFF),int((self.val >> 8)&0xFF),int((self.always_ffff)&0xFF),int((self.always_ffff >> 8)&0xFF)]
        
    def size(self):
        return 8

class TeamData:
    def __init__(self):
        self.unk_0 = [0]*8
        self.uniq = UniqueIdentityData()
        self.trainerTID = 0
        self.trainerSID = 0
        self.unk_1 = [0]*4
        self.trainerName = [0]*8
        self.unk_2 = [TeamDataUnk(), TeamDataUnk(), TeamDataUnk()]
        self.pokes = [TeamPokeData(), TeamPokeData(), TeamPokeData(), TeamPokeData(), TeamPokeData(), TeamPokeData()]
        """
        self.unknownZero  = [0]*0x72
        self.unknownData  = [0]*10
        self.unknownZero2 = [0]*0x1C
        self.curPokewalkerRouteName = [0]*16
        self.unknown = [0]*0x18
        """
        
    def decode(self, byteList):
        self.unk_0 = byteList[0:8]
        self.uniq.decode(byteList[8:48])
        self.trainerTID = byteList[48] + (byteList[49] << 8)
        self.trainerSID = byteList[50] + (byteList[51] << 8)
        self.unk_1 = byteList[52:56]
        self.trainerName = [(byteList[56] + (byteList[57]<<8)), (byteList[58] + (byteList[59]<<8)), (byteList[60] + (byteList[61]<<8)) , (byteList[62] + (byteList[63]<<8)),
                            (byteList[64] + (byteList[65]<<8)), (byteList[66] + (byteList[67]<<8)), (byteList[68] + (byteList[69]<<8)) , (byteList[70] + (byteList[71]<<8))]
        self.unk_2[0].decode(byteList[72:80])
        self.unk_2[1].decode(byteList[80:88])
        self.unk_2[2].decode(byteList[88:96])
        
        self.pokes[0].decode(byteList[96:152])
        self.pokes[1].decode(byteList[152:208])
        self.pokes[2].decode(byteList[208:264])
        self.pokes[3].decode(byteList[264:320])
        self.pokes[4].decode(byteList[320:376])
        self.pokes[5].decode(byteList[376:432])
        """
        self.unknownZero = byteList[432:546]
        self.unknownData = byteList[546:556]
        self.unknownZero2 = byteList[556:584]

        self.curPokewalkerRouteName = [(byteList[584] + (byteList[585]<<8)), (byteList[586] + (byteList[587]<<8)), (byteList[588] + (byteList[589]<<8)) , (byteList[590] + (byteList[591]<<8)),
                            (byteList[592] + (byteList[593]<<8)), (byteList[594] + (byteList[595]<<8)), (byteList[596] + (byteList[597]<<8)) , (byteList[598] + (byteList[599]<<8)),
                            (byteList[600] + (byteList[601]<<8)), (byteList[602] + (byteList[603]<<8)), (byteList[604] + (byteList[605]<<8)) , (byteList[606] + (byteList[607]<<8)),
                            (byteList[608] + (byteList[609]<<8)), (byteList[610] + (byteList[611]<<8)), (byteList[612] + (byteList[613]<<8)) , (byteList[614] + (byteList[615]<<8))]
                            
        self.unknown = byteList[616:640]      
        """
        
        
    def encode(self):
        return self.unk_0+self.uniq.encode()+[int(self.trainerTID&0xFF),int((self.trainerTID >> 8)&0xFF),int(self.trainerSID&0xFF),int((self.trainerSID >> 8)&0xFF)]+self.unk_1+sum([[int(self.trainerName[i]&0xFF),int((self.trainerName[i] >> 8)&0xFF)] for i in range(8)], []) + self.unk_2[0].encode() + self.unk_2[1].encode() + self.unk_2[2].encode() + self.pokes[0].encode() + self.pokes[1].encode() + self.pokes[2].encode() + self.pokes[3].encode() + self.pokes[4].encode() + self.pokes[5].encode()
        # + self.unknownZero + self.unknownData + self.unknownZero2 +  sum([[int(self.curPokewalkerRouteName[i]&0xFF),int((self.curPokewalkerRouteName[i] >> 8)&0xFF)] for i in range(16)], []) + self.unknown
        
    def size(self):
        return len(self.encode())


class PokemonSummary:
    def __init__(self):
        self.species = 0
        self.itemHeld = 0
        self.moves = [0]*4
        self.level = 0
        self.variantAndFlags = 0 # low 5 bits are variant (for unown, spinda, arceus, etc). mask 0x20 = female
        self.moreFlags = 0       # 0x02 = shiny, 0x01 = has form
        self.padding = 0
        
    def decode(self, byteList):
        self.species = byteList[0] + (byteList[1] << 8)
        self.itemHeld = byteList[2] + (byteList[3] << 8)
        self.moves[0] = byteList[4] + (byteList[5] << 8)
        self.moves[1] = byteList[6] + (byteList[7] << 8)
        self.moves[2] = byteList[8] + (byteList[9] << 8)
        self.moves[3] = byteList[10] + (byteList[11] << 8)
        self.level = byteList[12]
        self.variantAndFlags = byteList[13]
        self.moreFlags = byteList[14]
        self.padding = byteList[15]

    def encode(self):
        return [int(self.species&0xFF),int((self.species >> 8)&0xFF), int(self.itemHeld&0xFF),int((self.itemHeld >> 8)&0xFF), int(self.moves[0]&0xFF),int((self.moves[0] >> 8)&0xFF), int(self.moves[1]&0xFF),int((self.moves[1] >> 8)&0xFF), int(self.moves[2]&0xFF),int((self.moves[2] >> 8)&0xFF), int(self.moves[3]&0xFF),int((self.moves[3] >> 8)&0xFF),
                int(self.level&0xFF),int(self.variantAndFlags&0xFF),int(self.moreFlags&0xFF),int(self.padding&0xFF)]
                
    def size(self):
        return len(self.encode())
        
    def __str__(self):
        return "PokemonSummary(Type: "+str(self.species)+", LVL: "+str(self.level)+")" 
   
class RouteInfo:
    def __init__(self):
    
        self.poke = PokemonSummary()
        self.nickname = [0] * 11
        self.friendship = 0
        
        self.routeImageIdx = 0
        self.routeName = [0]*21
        
        self.routePokes = [PokemonSummary(), PokemonSummary(), PokemonSummary()]
        self.routePokeMinSteps = [0, 0, 0]
        self.routePokeChance = [0, 0, 0]
        self.padding = 0
        
        self.routeItems = [0]*10
        self.routeItemMinSteps = [0]*10
        self.routeItemChance = [0]*10
        
        
    def decode(self, byteList):
    
    
        self.poke.decode(byteList[0:16])
        self.nickname = [(byteList[16] + (byteList[17]<<8)), (byteList[18] + (byteList[19]<<8)), (byteList[20] + (byteList[21]<<8)) , (byteList[22] + (byteList[23]<<8)),
                         (byteList[24] + (byteList[25]<<8)), (byteList[26] + (byteList[27]<<8)), (byteList[28] + (byteList[29]<<8)) , (byteList[30] + (byteList[31]<<8)),
                         (byteList[32] + (byteList[33]<<8)), (byteList[34] + (byteList[35]<<8)), (byteList[36] + (byteList[37]<<8))]
        self.friendship = byteList[38]
        
        self.routeImageIdx = byteList[39]
                         
        self.routeName = [(byteList[40] + (byteList[41]<<8)), (byteList[42] + (byteList[43]<<8)), (byteList[44] + (byteList[45]<<8)) , (byteList[46] + (byteList[47]<<8)),
                          (byteList[48] + (byteList[49]<<8)), (byteList[50] + (byteList[51]<<8)), (byteList[52] + (byteList[53]<<8)) , (byteList[54] + (byteList[55]<<8)),
                          (byteList[56] + (byteList[57]<<8)), (byteList[58] + (byteList[59]<<8)), (byteList[60] + (byteList[61]<<8)) , (byteList[62] + (byteList[63]<<8)),
                          (byteList[64] + (byteList[65]<<8)), (byteList[66] + (byteList[67]<<8)), (byteList[68] + (byteList[69]<<8)) , (byteList[70] + (byteList[71]<<8)),
                          (byteList[72] + (byteList[73]<<8)), (byteList[74] + (byteList[75]<<8)), (byteList[76] + (byteList[77]<<8)) , (byteList[78] + (byteList[79]<<8)), 
                          (byteList[80] + (byteList[81]<<8))]
                          
        self.routePokes[0].decode(byteList[82:98])
        self.routePokes[1].decode(byteList[98:114])      
        self.routePokes[2].decode(byteList[114:130])        
        
        self.routePokeMinSteps = [(byteList[130] + (byteList[131]<<8)), (byteList[132] + (byteList[133]<<8)), (byteList[134] + (byteList[135]<<8))]
        self.routePokeChance   = byteList[136:139]
        self.padding           = byteList[139]
        
        self.routeItems = [(byteList[140] + (byteList[141]<<8)), (byteList[142] + (byteList[143]<<8)), (byteList[144] + (byteList[145]<<8)) , (byteList[146] + (byteList[147]<<8)),
                         (byteList[148] + (byteList[149]<<8)), (byteList[150] + (byteList[151]<<8)), (byteList[152] + (byteList[153]<<8)) , (byteList[154] + (byteList[155]<<8)),
                         (byteList[156] + (byteList[157]<<8)), (byteList[158] + (byteList[159]<<8))]
                         
        self.routeItemMinSteps = [(byteList[160] + (byteList[161]<<8)), (byteList[162] + (byteList[163]<<8)), (byteList[164] + (byteList[165]<<8)) , (byteList[166] + (byteList[167]<<8)),
                         (byteList[168] + (byteList[169]<<8)), (byteList[170] + (byteList[171]<<8)), (byteList[172] + (byteList[173]<<8)) , (byteList[174] + (byteList[175]<<8)),
                         (byteList[176] + (byteList[177]<<8)), (byteList[178] + (byteList[179]<<8))]
                         
        self.routeItemChance  = byteList[180:190]


    def encode(self):
        return self.poke.encode() + sum([[int(self.nickname[i]&0xFF),int((self.nickname[i] >> 8)&0xFF)] for i in range(11)], []) + [int(self.friendship&0xFF), int(self.routeImageIdx&0xFF)]+ sum([[int(self.routeName[i]&0xFF),int((self.routeName[i] >> 8)&0xFF)] for i in range(21)], []) + self.routePokes[0].encode() + self.routePokes[1].encode() + self.routePokes[2].encode() + sum([[int(self.routePokeMinSteps[i]&0xFF),int((self.routePokeMinSteps[i] >> 8)&0xFF)] for i in range(3)], []) + self.routePokeChance + [int(self.padding&0xFF)] + sum([[int(self.routeItems[i]&0xFF),int((self.routeItems[i] >> 8)&0xFF)] for i in range(10)], [])  + sum([[int(self.routeItemMinSteps[i]&0xFF),int((self.routeItemMinSteps[i] >> 8)&0xFF)] for i in range(10)], []) + self.routeItemChance
        
    def size(self):
        return len(self.encode())

class EventLogItem:
    def __init__(self):
    
    
        self.eventTime = 0
        self.unk_0 = 0
        self.unk_2 = 0
        self.walkingPokeSpecies = 0
        self.caughtSpecies = 0
        self.extraData = 0
        self.remoteTrnrName = [0]*8
        self.pokeNick = [0]* 11
        self.remPokeNick = [0]* 11
        self.routeImageIdx = 0
        self.pokeFriendship = 0
        self.watts = 0
        self.remoteWatts = 0
        self.stepCount = 0
        self.remoteStepCount = 0
        self.eventType = 0
        self.genderAndForm = 0
        self.caughtGenderAndForm = 0
        self.padding = 0
        
        
    def decode(self, byteList):
    
        self.eventTime = byteList[3] + (byteList[2] << 8) + (byteList[1] << 16) + (byteList[0] << 24)
        self.unk_0     = byteList[4] + (byteList[5] << 8) + (byteList[6] << 16) + (byteList[7] << 24)
        self.unk_2     = byteList[8] + (byteList[9] << 8) 
        self.walkingPokeSpecies = byteList[10] + (byteList[11] << 8) 
        self.caughtSpecies = byteList[12] + (byteList[13] << 8) 
        self.extraData = byteList[14] + (byteList[15] << 8) 
        self.remoteTrnrName = [(byteList[16] + (byteList[17]<<8)), (byteList[18] + (byteList[19]<<8)), (byteList[20] + (byteList[21]<<8)) , (byteList[22] + (byteList[23]<<8)),
                         (byteList[24] + (byteList[25]<<8)), (byteList[26] + (byteList[27]<<8)), (byteList[28] + (byteList[29]<<8)), (byteList[30] + (byteList[31]<<8))]
                         
        self.pokeNick = [(byteList[32] + (byteList[33]<<8)), (byteList[34] + (byteList[35]<<8)), (byteList[36] + (byteList[37]<<8)) , (byteList[38] + (byteList[39]<<8)),
                         (byteList[40] + (byteList[41]<<8)), (byteList[42] + (byteList[43]<<8)), (byteList[44] + (byteList[45]<<8)) , (byteList[46] + (byteList[47]<<8)),
                         (byteList[48] + (byteList[49]<<8)), (byteList[50] + (byteList[51]<<8)), (byteList[52] + (byteList[53]<<8))]       
                         
        self.remPokeNick = [(byteList[54] + (byteList[55]<<8)), (byteList[56] + (byteList[57]<<8)), (byteList[58] + (byteList[59]<<8)) , (byteList[60] + (byteList[61]<<8)),
                         (byteList[62] + (byteList[63]<<8)), (byteList[64] + (byteList[65]<<8)), (byteList[66] + (byteList[67]<<8)) , (byteList[68] + (byteList[69]<<8)),
                         (byteList[70] + (byteList[71]<<8)), (byteList[72] + (byteList[73]<<8)), (byteList[74] + (byteList[75]<<8))]      
                         
        self.routeImageIdx = byteList[76]
        self.pokeFriendship = byteList[77]            
        self.watts         = byteList[79] + (byteList[78] << 8) 
        self.remoteWatts   = byteList[81] + (byteList[80] << 8) 
        self.stepCount       = byteList[85] + (byteList[84] << 8) + (byteList[83] << 16) + (byteList[82] << 24)
        self.remoteStepCount = byteList[89] + (byteList[88] << 8) + (byteList[87] << 16) + (byteList[86] << 24)
        self.eventType = byteList[90]
        self.genderAndForm = byteList[91]
        self.caughtGenderAndForm = byteList[92]
        self.padding = byteList[93]
        
    def encode(self):
        return [int((self.eventTime >> 24)&0xFF),int((self.eventTime >> 16)&0xFF),int((self.eventTime >> 8)&0xFF),int((self.eventTime)&0xFF),
        int(self.unk_0&0xFF),int((self.unk_0 >> 8)&0xFF),int((self.unk_0 >> 16)&0xFF),int((self.unk_0 >> 24)&0xFF),
        int(self.unk_2&0xFF),int((self.unk_2 >> 8)&0xFF),
        int(self.walkingPokeSpecies&0xFF),int((self.walkingPokeSpecies >> 8)&0xFF),
        int(self.caughtSpecies&0xFF),int((self.caughtSpecies >> 8)&0xFF),
        int(self.extraData&0xFF),int((self.extraData >> 8)&0xFF),
        ] + sum([[int(self.remoteTrnrName[i]&0xFF),int((self.remoteTrnrName[i] >> 8)&0xFF)] for i in range(8)], []) + sum([[int(self.pokeNick[i]&0xFF),int((self.pokeNick[i] >> 8)&0xFF)] for i in range(11)], []) + sum([[int(self.remPokeNick[i]&0xFF),int((self.remPokeNick[i] >> 8)&0xFF)] for i in range(11)], []) + [
           int(self.routeImageIdx&0xFF),
           int(self.pokeFriendship&0xFF),
           int((self.watts >> 8)&0xFF),int((self.watts)&0xFF),
           int((self.remoteWatts >> 8)&0xFF),int((self.remoteWatts)&0xFF),
           int((self.stepCount >> 24)&0xFF),int((self.stepCount >> 16)&0xFF),int((self.stepCount >> 8)&0xFF),int((self.stepCount)&0xFF),
           int((self.remoteStepCount >> 24)&0xFF),int((self.remoteStepCount >> 16)&0xFF),int((self.remoteStepCount >> 8)&0xFF),int((self.remoteStepCount)&0xFF),
           int(self.eventType&0xFF),
           int(self.genderAndForm&0xFF),
           int(self.caughtGenderAndForm&0xFF),
           int(self.padding&0xFF),
        ]
    def size(self):
        return len(self.encode())

