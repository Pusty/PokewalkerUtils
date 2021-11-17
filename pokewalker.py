from pokewalker_header import *
from pokewalker_eeprom import *

import os.path
# https://dmitry.gr/?r=05.Projects&proj=28.%20pokewalker

mode = MODE_NORMAL

class PokeWalker:

    def __init__(self):
        self.sessionKey = 0
        self.deviceMemory = [0]*0x10000
        self.failed = False
        self.resetDataAfter = False
    
    def loadFromFile(self, uniqID):
        print("Loading "+str(uniqID)+" ROM")
        fileName = "eeprom.bin"
        if os.path.isfile(fileName):
            f = open(fileName, "rb")
            data = f.read()
            f.close()
            for i in range(len(data)):
                self.deviceMemory[i] = data[i]

    def saveToFile(self, uniqID):
        print("Saving "+str(uniqID)+" ROM")
        fileName = "eeprom.bin"
        f = open(fileName, "wb")
        f.write(bytes(self.deviceMemory))
        f.close()
        
        
    def createIDENTITYDATASENDRSP(self, data, type):

        if type == CMD_IDENTITY_DATA_SEND: # for some reason send3 does weird stuff
            self.deviceMemory[0x00ED:0x0155] = data   # self.identity.decode(data)
            
        if mode == MODE_DEBUG: print(data)
        
        
        idrsp = PokePacket()
        if type == CMD_IDENTITY_DATA_SEND:
            idrsp.cmd = CMD_IDENTITY_DATA_SEND_RSP  # set initial identiy
        elif type == CMD_IDENTITY_DATA_SEND2:
            idrsp.cmd = CMD_IDENTITY_DATA_SEND_RSP2 # take back from stroll
        elif type == CMD_IDENTITY_DATA_SEND3:
            idrsp.cmd = CMD_IDENTITY_DATA_SEND_RSP3 # take back items from walk
            self.resetDataAfter = True # am I missing something or where does gift stuff get reset?
        elif type == CMD_IDENTITY_DATA_SEND4:
            idrsp.cmd = CMD_IDENTITY_DATA_SEND_RSP4 # take another stroll
        idrsp.detail = DETAIL_DIR_FROM_WALKER
        idrsp.session = self.sessionKey
        idrsp.crc = idrsp.calcCRC()
        return idrsp.encode()
        
        
    def createREADRSP(self, data):
        
        addr = (data[0] << 8) + data[1]
        len = data[2]
        if mode == MODE_DEBUG: print(hex(addr)+": "+str(len))
        
        odata = self.deviceMemory[addr:addr+len] #[0]*len
        
        rrsp = PokePacket()
        rrsp.cmd = CMD_EEPROM_READ_RSP
        rrsp.detail = DETAIL_DIR_FROM_WALKER
        rrsp.session = self.sessionKey
        rrsp.crc = crcAlgorithm(odata, rrsp.calcCRC())
        return rrsp.encode() + odata
        
    def createWRITERSP(self, data, packet):
        #print(data)
        addr = 0
        size = 128
        decompress = False
        
        if packet.cmd == CMD_EEPROM_WRITE_COMPRESSED_REQ2:
            addr = packet.detail << 8
            decompress = True
        elif packet.cmd == CMD_EEPROM_WRITE_REQ2:
            addr = packet.detail << 8
        elif packet.cmd == CMD_EEPROM_WRITE_REQ:
            addr = (packet.detail << 8) + data[0]
            data = data[1:]
            size = len(data)
        elif packet.cmd == CMD_EEPROM_WRITE_COMPRESSED_REQ:
            addr = (packet.detail << 8) + 0x80
            decompress = True
        elif packet.cmd == CMD_EEPROM_WRITE_REQ3:
            addr = (packet.detail << 8) + 0x80
       
        # https://projectpokemon.org/home/docs/other/compression-r9/
        if decompress:
            data = LZ77_decompress(data)
        
        for index in range(size):
            value = 0
            if index < len(data):
                value = data[index]
            self.deviceMemory[addr+index] = value
        
        wrsp = PokePacket()
        wrsp.cmd = CMD_EEPROM_WRITE_RSP
        wrsp.detail = DETAIL_DIR_FROM_WALKER
        wrsp.session = self.sessionKey
        wrsp.crc = wrsp.calcCRC()
        return wrsp.encode()
        
    def createPong(self):

        pong = PokePacket()
        pong.cmd = CMD_PONG
        pong.detail = DETAIL_DIR_FROM_WALKER
        pong.session = self.sessionKey
        pong.crc = pong.calcCRC()
        return pong.encode()
        
    def createSTARTWALKRSP(self, type):

        id = IdentityData()
        id.decode(self.deviceMemory[0x00ED:0x0155])
        id.unk_0 = 1
        id.unk_1 = 1
        id.unk_2 = 7
        id.unk_3 = 7
        id.flags = 0x1 | 0x2 # | 0x4 
        id.unk_8 = 2
        self.deviceMemory[0x00ED:0x0155] = id.encode()
        
        
        # copy from staging to actual memory
        for index in range(0x2900): # route data
            self.deviceMemory[0x8F00+index] = self.deviceMemory[0xD700+index]
            
        for index in range(0x280): # team data
            self.deviceMemory[0xCC00+index] = self.deviceMemory[0xD480+index]
            
        for index in range(0x1568): # clear peer team data
            self.deviceMemory[0xDE24+index] = 0
            
            
        
        # add a LogEvtWalkStarted 
        
        #print(self.identity.encode())

        startWalk = PokePacket()
        startWalk.cmd = type #CMD_START_WALK [echo back]
        startWalk.detail = DETAIL_DIR_FROM_WALKER
        startWalk.session = self.sessionKey
        startWalk.crc = startWalk.calcCRC()
        return startWalk.encode()
        
    def createENDWALKRSP(self):

        id = IdentityData()
        id.decode(self.deviceMemory[0x00ED:0x0155])
        id.unk_0 = 1
        id.unk_1 = 1
        id.unk_2 = 7
        id.unk_3 = 7
        id.flags = 0x1
        id.unk_8 = 0
        self.deviceMemory[0x00ED:0x0155] = id.encode()


        self.resetDataAfter = True
    
        
        stopWalk = PokePacket()
        stopWalk.cmd = CMD_END_WALK_RSP
        stopWalk.detail = DETAIL_DIR_FROM_WALKER
        stopWalk.session = self.sessionKey
        stopWalk.crc = stopWalk.calcCRC()
        return stopWalk.encode()
        
        
    def createCOMPLETEDRSP(self):
        completed = PokePacket()
        completed.cmd = CMD_COMPLETED_CONNECTION_RSP
        completed.detail = DETAIL_DIR_FROM_WALKER
        completed.session = self.sessionKey
        completed.crc = completed.calcCRC()
        return completed.encode()
      
    def createIDENTITYDATARSP(self):
        res = PokePacket()
        res.cmd = CMD_IDENTITY_DATA_RSP
        res.detail = DETAIL_DIR_FROM_WALKER
        res.session = self.sessionKey
        
        #identity = IdentityData()
        
        
        id = IdentityData()
        id.decode(self.deviceMemory[0x00ED:0x0155])
        data = id.encode()
        if mode == MODE_DEBUG: print(id.uniq.data)
        
        res.crc = crcAlgorithm(data, res.calcCRC())
        
        return res.encode()+data
      
    def createSYNACK(self):
        synack = PokePacket()
        synack.cmd = CMD_POKEWALKER_SYNACK
        synack.detail = DETAIL_DIR_FROM_WALKER
        synack.session = 0 # own key = 0
        synack.crc = synack.calcCRC()
        return synack.encode()


    def parse(self, packet):
        pokePacket = PokePacket()
        pokePacket.decode(packet[0:8])

        if pokePacket.cmd == CMD_POKEWALKER_SYN:
            self.sessionKey = pokePacket.session
            if mode == MODE_DEBUG: print("Setting session key: "+hex(self.sessionKey))
            self.loadFromFile(0)
            self.resetDataAfter = False
            return self.createSYNACK()
        elif pokePacket.cmd == CMD_IDENTITY_DATA_REQ:
            if mode == MODE_DEBUG:  print("Returning Identify...")
            return self.createIDENTITYDATARSP()
        elif pokePacket.cmd == CMD_UNIQUE_ID_RESET:
            self.deviceMemory = [0]*0x10000
            print("Reset Device: "+str(packet[8:]))
            return []
        elif pokePacket.cmd == CMD_DISCONNECT:
            if mode == MODE_DEBUG: print("Disconnect Device")
            
            # Zero Walk Results Here?
            if self.resetDataAfter:
                self.deviceMemory[0xCE80:0xF6F8] = [0]*0x2878
                
            if not self.failed:
                self.saveToFile(0)
                
            return None
        elif pokePacket.cmd == CMD_IDENTITY_DATA_SEND:
            if mode == MODE_DEBUG: print("Setting Identity..")
            return self.createIDENTITYDATASENDRSP(packet[8:], pokePacket.cmd)
        elif pokePacket.cmd == CMD_IDENTITY_DATA_SEND2:
            if mode == MODE_DEBUG: print("Setting Identity2..")
            return self.createIDENTITYDATASENDRSP(packet[8:], pokePacket.cmd)
        elif pokePacket.cmd == CMD_IDENTITY_DATA_SEND3:
            if mode == MODE_DEBUG: print("Setting Identity3..") 
            return self.createIDENTITYDATASENDRSP(packet[8:], pokePacket.cmd)
        elif pokePacket.cmd == CMD_IDENTITY_DATA_SEND4:
            if mode == MODE_DEBUG: print("Setting Identity4..") 
            return self.createIDENTITYDATASENDRSP(packet[8:], pokePacket.cmd)
        elif pokePacket.cmd == CMD_EEPROM_WRITE_COMPRESSED_REQ:
            if mode == MODE_DEBUG: print("Writing Fixed Size Compressed EEPROM (0x80)..")
            return self.createWRITERSP(packet[8:], pokePacket)
        elif pokePacket.cmd == CMD_EEPROM_WRITE_COMPRESSED_REQ2:
            if mode == MODE_DEBUG: print("Writing Fixed Size Compressed EEPROM (0x00)..")
            return self.createWRITERSP(packet[8:], pokePacket)
        elif pokePacket.cmd == CMD_EEPROM_WRITE_REQ2:
            if mode == MODE_DEBUG: print("Writing Fixed Size EEPROM (0x00)..")
            return self.createWRITERSP(packet[8:], pokePacket)
        elif pokePacket.cmd == CMD_EEPROM_WRITE_REQ3:
            if mode == MODE_DEBUG: print("Writing Fixed Size EEPROM (0x80)..")
            return self.createWRITERSP(packet[8:], pokePacket)
        elif pokePacket.cmd == CMD_EEPROM_WRITE_REQ:
            if mode == MODE_DEBUG: print("Writing Random Size EEPROM..")
            return self.createWRITERSP(packet[8:], pokePacket)
        elif pokePacket.cmd == CMD_PING:
            if mode == MODE_DEBUG: print("Ping!")
            return self.createPong()
        elif pokePacket.cmd == CMD_START_WALK:
            if mode == MODE_DEBUG: print("Start Walk!")
            return self.createSTARTWALKRSP(pokePacket.cmd)
        elif pokePacket.cmd == CMD_START_WALK2:
            if mode == MODE_DEBUG: print("Start Walk2!")
            return self.createSTARTWALKRSP(pokePacket.cmd)
        elif pokePacket.cmd == CMD_END_WALK:
            if mode == MODE_DEBUG: print("End Walk!")
            return self.createENDWALKRSP()
        elif pokePacket.cmd == CMD_ERROR_CONNECTION:
            print("Error Connecting")
            self.failed = True
            return []
        elif pokePacket.cmd == CMD_ERROR_CONNECTION2:
            print("Error Connecting")
            self.failed = True
            return []
        elif pokePacket.cmd == CMD_ERROR_CONNECTION3:
            print("Error Connecting")
            self.failed = True
            return []
        elif pokePacket.cmd == CMD_COMPLETED_CONNECTION:
            if mode == MODE_DEBUG: print("Completed Connection")
            return self.createCOMPLETEDRSP()
        elif pokePacket.cmd == CMD_EEPROM_READ_REQ:
            if mode == MODE_DEBUG: print("Reading EEPROM")
            return self.createREADRSP(packet[8:])
        else:
            print("UNKNOWN COMMAND %02X" % pokePacket.cmd)
            self.failed = True
            return [] 
        
        return

    def answerPacket(self, inp):
        
        inpList = [c^POKEWALKER_KEY for c in bytes.fromhex(inp.decode("utf-8"))]
        #print("> "+str(inpList))
        
        response = self.parse(inpList)
        #print("< "+str(response))
        
        if response == None: return None
        
        outList = response #[0xF8, 0x02, 0x04, 0xf8, 0x00, 0x00, 0x00, 0x00]
        output = b''.join(b"%02x" % (c ^ POKEWALKER_KEY) for c in outList)
        return output
        
    
if __name__ == "__main__":
    pk = PokeWalker()
    pk.answerPacket("50abb2b3efde7335") # CMD_POKEWALKER_SYNACK
    pk.answerPacket("8aabbd95efde7335") # 0x20
    pk.answerPacket("80ab7e42c083e670aaaaaaaaaaaaaaaa189c93aae6709efcdfc1133e8ba88cafaa838caaaaaaaaaaaaacaaaa5585aaaa")
    pk.answerPacket("5eabad01c083e670")
    pk.answerPacket("98ab577de6658090abaaaaaaabaaaaaaadaaadaa34e09acdaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa9dabefabfcabe7ab5555aaaaaaaaaaaaaaaaaaaaaaaaaaaa8d61a3c5aaaaaaaa")
    pk.answerPacket("2aa89805e8dbe8f0ba2aaaaaaaaaaa4a4a5abab2a2abb2ba5a4a4aaaaaaaabaaada9a5aeb2a2b6aebaa5a9ad8aa5aaaa9abaac9aba525252eaa79abeb58aa5b5eab7da9ad2a2b2a8a2322252da5a8a95b6aaa6b4a0b5a3b3a2b38fa2b2cab53222bab5da8af5baa4acb4aab1b3a2b5adeaa5aac5")
    pk.answerPacket("aaa9d0122a4923cbba2aaaaaaaaaaa6a6a5a9a92a2ae525252aaaa8aabada9aaada8aca8b5a5b5a8ceac8abbaab32232baaba2b22e8a8ba7aeb3a2baabb5ade2a58a9b5a5a9ab512ba9a238aeba5adb50ab5b2a2baabae72625292d2eacbb6a6aeb5a9adaaab8ac5")
    pk.answerPacket("a8af93c300e193c99494969692929a9acacadadad2d2d6d6d6d6d2d2dadacaca9a9a82828e8e888888888e8e82829a9aa6a6b6b69696d6d6d6d69696b6b6a6a6acaca4a4b4b494949494b4b4a4a4acaca6a6bebe8e8eeeeeeeee8e8ebebea6a6aaaab2b29696d4d455555555aaaaaaaaaaaaaaaab2b29696d4d455555555aaaaaaaab2b28e8ee8e8")
    pk.answerPacket("2824de66b1d384c1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    pk.answerPacket("8eabe2d1757dddc7")
    pk.answerPacket("92ab303e668c3ada")
    pk.answerPacket("5eab269f9caea12e")
    pk.answerPacket("eaab70da735976a8abaaaaaaabaaaaaaadaaadaa34e09acd7508f77bcbeee2bb724fb9b883d7e3aac5fef04e83fc1e658e110321b095f303d85f39651c42e39baaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa9dabefabfcabe7ab5555aaaaaaaaaaaaaaaaaaaaaaaaaaaa8d61b418aaaaaaaa")
    pk.answerPacket("a6a8f67dd4fe3ea925aa80")
    
    """
> [42, 1, 212, 232, 106, 41, 76, 218, 0, 0, 0, 0, 0, 0, 0, 0, 178, 54, 57, 0, 76, 218, 52, 86, 117, 107, 185, 148, 33, 2, 38, 5, 0, 41, 38, 0, 0, 0, 0, 0, 0, 6, 0, 0, 255, 47, 0, 0]
UNKNOWN COMMAND 2A
< [0]
> [244, 1, 7, 171, 106, 41, 76, 218]
UNKNOWN COMMAND F4
< [0]
> [50, 1, 253, 215, 76, 207, 42, 58, 1, 0, 0, 0, 1, 0, 0, 0, 7, 0, 7, 0, 158, 74, 48, 103, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 55, 1, 69, 1, 86, 1, 77, 1, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 39, 203, 9, 111, 0, 0, 0, 0]
UNKNOWN COMMAND 32
< []
> [128, 2, 50, 175, 66, 113, 66, 90, 16, 128, 0, 0, 0, 0, 0, 224, 224, 240, 16, 24, 8, 1, 24, 16, 240, 224, 224, 0, 0, 0, 1, 0, 7, 3, 15, 4, 24, 8, 28, 4, 16, 15, 3, 7, 32, 15, 0, 0, 48, 16, 6, 48, 16, 248, 248, 248, 64, 13, 48, 20, 31, 32, 15, 31, 64, 29, 112, 48, 120, 8, 24, 2, 8, 152, 136, 248, 112, 240, 32, 63, 28, 0, 12, 30, 10, 31, 9, 25, 8, 25, 37, 8, 24, 96, 31, 152, 136, 16, 31, 112, 32, 95, 16, 14, 6, 30, 0, 27, 25, 8, 31, 7, 64, 15, 0, 111]
UNKNOWN COMMAND 80
"""

