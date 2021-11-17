#!/usr/bin/env python

import socket
import threading

import pokewalker



def newConnection(c,addr):
    #reload(pokewalker)
    walker = pokewalker.PokeWalker()
    while True:
        msg = c.recv(1024)
        if not msg: break
        #print addr, ' >> ', msg
        response = walker.answerPacket(msg)
        if response == None: break
        if len(response) > 0:
            c.send(response+b"\n")
    c.close()

TCP_IP = '127.0.0.1'
TCP_PORT = 54545

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(5)

while True:
   c, addr = s.accept() 
   print('Got connection from', addr)
   threading.Thread(target=newConnection, args=(c,addr)).start()
   #thread.start_new_thread(newConnection,(c,addr))
s.close()
