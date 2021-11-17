-- http://tasvideos.org/LuaScripting.html
-- https://github.com/dude22072/PokeStats/blob/master/LUA%20scripts/Pokestats%20Gen%204%20and%205.lua
-- https://dmitry.gr/?r=05.Projects&proj=28.%20pokewalker


--TCP stuff
local host, port = "127.0.0.1", 54545
local socket = require("socket")
local tcp = assert(socket.tcp())
tcp:connect(host, port)
--tcp:settimeout(0)
print(tcp:getpeername())




-- mode 0: send SYN, mode 1: write packet, mode 2: read packet, mode 1...
packetMode = 0

-- https://github.com/TASVideos/desmume/blob/d854909b040b021ef027d53cbfd6555b175c1bb8/desmume/src/mc.cpp
-- BM_CMD_IRDA = IRDA

--function mW()
--    print("    W:" .. memWrite)
--end

--memory.registerwrite(0x40001A2, 1, mW)

packetIndex = 0


currentMode = 0
currentPacket = ""
currentPacketSize = 0


--ROM:020DDE68 ; 24:   *a1[2] = v6;
--ROM:020DDE68                 LDR             R1, =AUXSPIDATA
--ROM:020DDE6C                 LDR             R0, [R6,#8]
--ROM:020DDE70 ; 23:   v6 = AUXSPIDATA;
--ROM:020DDE70                 LDRH            R1, [R1]
--ROM:020DDE74                 STRB            R1, [R0]


function readAUXSPIDATA()
    memRead  = 0
    
    
    if packetMode == 0 then
        if packetIndex == 0 then
            memRead = 1
        else
            memRead = XOR(0xFC,0xAA)
        end
        packetIndex = packetIndex + 1
        if packetIndex == 2 then
            packetMode = 0
        end
    end
    
    if packetMode == 2 then  -- if reading packet, load from received command
        if packetIndex == 0 then
            memRead = currentPacketSize
        else
            memRead = string.sub(currentPacket, packetIndex*2-1, packetIndex*2)
            memRead = tonumber(memRead, 16)
            --memRead = XOR(memRead,0xAA)
        end
        packetIndex = packetIndex + 1
        if packetIndex == currentPacketSize+1 then
            packetMode = 3 -- stand by
        end
    end
    
    --print("    R:" .. memRead)

    
    memory.setregister("r1", memRead)
end
memory.registerrun(0x20DDE74 , readAUXSPIDATA)

--ROM:020DDDA4                 LDR             R1, =AUXSPIDATA
--ROM:020DDDA8                 LDRB            R0, [R0]
--ROM:020DDDAC                 STRH            R0, [R1]
--ROM:020DDDB0                 LDR             R0, [R6,#4]

function writeAUXSPIDATA()
    memWrite  = memory.getregister("r0")
    
    --print("    W:" .. memWrite)
    
    if currentMode == 1 then -- if writing packet, save written bytes
        currentPacket = currentPacket..string.sub(bit.tohex(memWrite),7,8) -- append hex string
    end
    
end
memory.registerrun(0x20DDDAC, writeAUXSPIDATA)

function packetRead()
    if packetMode == 1 then
        packetMode = 2
        -- read packet
        local line, err = tcp:receive("*l")
        currentPacket = line --"f80204f800000000"
        currentPacketSize = string.len(currentPacket)/2
        print("Received Packet: "..currentPacket)
    elseif packetMode == 1 or packetMode == 2 then
        packetMode = 0 -- send SYN
    end
    
    packetIndex = 0 -- reset packet index
    currentMode = 0 -- set mode to READ
    --print("Start reading packet...")
end
memory.registerrun(0x20DDE94, packetRead)


function packetReadEnd()
    --print("End of reading packet...")
    print("resultLen "..memory.getregister("r0"))
end
memory.registerrun(0x20DDFC0, packetReadEnd)

function packetWrite()
    packetMode = 1
    currentPacket = ""
    currentPacketSize = 0
    currentMode = 1 -- set mode to WRITE
    --print("Start writing packet...")
end
memory.registerrun(0x20DDFE0, packetWrite)

function packetWriteEnd()
    --print("End of writing packet...")
    currentPacket = string.sub(currentPacket, 3) -- trim of the initial command
    currentPacketSize = string.len(currentPacket)/2
    -- send packet
    tcp:send(currentPacket)
    print("Send Packet: "..currentPacket)
    
    if XOR(tonumber(string.sub(currentPacket, 1, 2), 16), 0xAA) == 0xF4 then
        packetMode = 4 -- Do nothing
    end
    
end
memory.registerrun(0x20DE0A8, packetWriteEnd)


--function debugTest2()
--    print("firstByte "..memory.getregister("r4"))
--end
--memory.registerrun(0x20DDF08 , debugTest2)


--function debugTest3()
--    print("checksum ->  "..memory.getregister("r0").." <=> "..memory.getregister("r4"))
--    print(" => ".. memory.readbyte(0x21FFA18).." "..memory.readbyte(0x21FFA19).." "..memory.readbyte(0x21FFA1A).." "..memory.readbyte(0x21FFA1B).." "..memory.readbyte(0x21FFA1C).." "..memory.readbyte(0x21FFA1D).." "..memory.readbyte(0x21FFA1E).." "..memory.readbyte(0x21FFA1F))
--end
--memory.registerrun(0x021E5B68 , debugTest3)

--function debugTest4()
--    print("lenCheck1 ->  "..memory.getregister("r0").." size: "..memory.getregister("r4"))
--    print(" => ".. memory.readbyte(0x21FFA18).." "..memory.readbyte(0x21FFA19).." "..memory.readbyte(0x21FFA1A).." "..memory.readbyte(0x21FFA1B).." "..memory.readbyte(0x21FFA1C).." "..memory.readbyte(0x21FFA1D).." "..memory.readbyte(0x21FFA1E).." "..memory.readbyte(0x21FFA1F))
--end
--memory.registerrun(0x21E5BA6 , debugTest4)

function debugTest5()
    print("commandReceived: "..memory.getregister("r0"))
end

memory.registerrun(0x21E5BFA, debugTest5)

function debugTest6()
    print("waitForCommand - isConnected? "..memory.readbyte(0x21FFA0C))
end
memory.registerrun(0x21E5B98, debugTest6)


--function debugTest7()
--    print("checksum len - "..memory.getregister("r1"))
--end
--memory.registerrun(0x21E5B5E , debugTest7)


local function fn()
	gui.text(2,2,"Pokewalker Connected")
end
gui.register(fn)


--- dword_21FF9E4   DCD 0x622A1B2    device seed?
--- https://github.com/TASVideos/desmume/blob/d854909b040b021ef027d53cbfd6555b175c1bb8/desmume/src/mc.cpp