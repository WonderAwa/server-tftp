# -- coding: utf-8 --
"""
TFTP Module.
"""

import socket
import sys

########################################################################
#                          COMMON ROUTINES                             #
########################################################################

""" Send a request WRQ to put a file"""
def requestWRQ(sock,addr,filename,mode,blksize):
    blocksize='blksize'
    msg= b'\x00\x02'+ bytes(filename.encode()) +bytes(1)+ bytes(mode.encode())+bytes(1)+bytes(blocksize.encode())+bytes(1)+bytes(str(blksize).encode())+bytes(1)
    sock.sendto(msg,addr)

""" Send a request RRQ to get a file"""
def requestRRQ(sock,addr,filename,mode,blksize):
    blocksize='blksize'
    msg= b'\x00\x01'+ bytes(filename.encode()) +bytes(1)+ bytes(mode.encode())+bytes(1)+bytes(blocksize.encode())+bytes(1)+bytes(str(blksize).encode())+bytes(1)
    sock.sendto(msg,addr)

""" send an acquittal"""
def send_ack(sock, addr, i):
    msg= b'\x00\x04'+bytes(1)+bytes([i])
    sock.sendto(msg,addr)

""" send a block of file """
def send_data(sock,addr,data,i):
    msg=b'\x00\x03'+bytes(1)+bytes([i])+data
    sock.sendto(msg,addr)

"""send a message of error"""
def sendERROR(sock,addr,errorCode,errorMSG) : 
    msg= b'\x00\x05'+ bytes([errorCode]) + bytes(errorMSG.encode())+bytes(1)
    sock.sendto(msg,addr)
   
""" decompose the received message"""
def recevoir(msg):
    dic= {} 
    msg1 = msg[0:2]                               
    msg2 = msg[2:]                                
    opcode = int.from_bytes(msg1, byteorder='big')
    args = msg2.split(b'\x00')     
    mode = args[1]
    filename = args[0].decode('ascii')
    if opcode ==1 or opcode ==2:
        dic["opcode"]=opcode
        dic["filename"]= filename
        dic["mode"]=mode
        if len(args)>3:
            blksize= int(args[3].decode())
            print(blksize)
            dic["blksize"]= blksize
    if opcode == 5:
        dic["opcode"]=opcode
    if opcode ==4:
       dic["opcode"]=opcode
       nb_ack= int.from_bytes(msg2,byteorder='big')
       dic["nb_ack"]=nb_ack
    if opcode == 3:
        dic["opcode"]=opcode
        args1 = msg2[0:2]
        args= msg2[2:]
        nb_data=int.from_bytes(args1,byteorder='big')
        dic["nb_data"]=nb_data
        data= args
        dic["data"]=data
    return dic

""" Receive file"""
def recv_file(filename,sock,blksize):
    file= open(filename,"wb")
    while True:
        msg,addr = sock.recvfrom(1500)
        dic=recevoir(msg)
        if dic["opcode"]== 3:
            file.write(dic["data"])
            send_ack(sock, addr, dic["nb_data"])
        if len(dic["data"]) < blksize:
            break
    file.close()


""" send file """
def send_file(filename,sock,blksize,addr):
    i=1
    file=open(filename,'rb')
    while True:
        data= file.read(blksize)
        send_data(sock,addr,data,i)
        msg,addr = sock.recvfrom(1500)
        dic=recevoir(msg)
        if dic["opcode"]== 4 and dic["nb_ack"]==i:
            i=i+1
        if len(data) < blksize:
            break
    file.close()
 

########################################################################
#                             SERVER SIDE                              #
########################################################################

def runServer(addr, timeout, thread):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 6969))
    while True:
        msg,addr = s.recvfrom(1500)
        dic=recevoir(msg)
        if len(dic)>3:
            blksize=dic["blksize"]
        else:
            blksize=512
        sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        ###GET###
        if dic["opcode"] ==1:
            send_file(dic["filename"],sock,blksize,addr)

        ###PUT###
        if dic["opcode"] == 2:
            send_ack(sock, addr, 0)
            recv_file(dic["filename"],sock,blksize)
        sock.close()
    s.close()


########################################################################
#                             CLIENT SIDE                              #
########################################################################


def put(addr, filename, targetname, blksize, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    mode='octet'
    requestWRQ(s,addr,targetname,mode,blksize)
    msg,addr=s.recvfrom(1500)
    send_file(filename,s,blksize,addr)
    s.close
    pass

########################################################################
def get(addr, filename, targetname, blksize, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    mode='octet'
    requestRRQ(s,addr,filename,mode,blksize)
    recv_file(targetname,s,blksize)
    s.close()
    pass
