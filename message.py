#/usr/bin/env python2

import socket
import select
import struct

import toClient
import fromClient

messages = [toClient.GreetingMessage,
        toClient.InitialGameData,
        toClient.TurnData,
        toClient.SoldierData,
        toClient.RemoveSoldierData,
        toClient.SoldierAPData,
        toClient.GameOverData,

        fromClient.ChatMessage,
        fromClient.ServerConfiguration,
        fromClient.StartGame,
        fromClient.GetTeam,
        fromClient.EndOfTurnCommand,
        fromClient.MoveForwardCommand,
        fromClient.TurnCommand,
        fromClient.ShootCommand]
msgids = dict()
for m in messages:
    msgids[m.msgid] = m

msg_fmtstring = '>LL'
msg_headerlen = struct.calcsize(msg_fmtstring)

debug = True

def recvMessage(sock):
    msgs = []
    buf = ''
    while True:
        try:
            while len(buf) < msg_headerlen:
                newbuf = sock.recv(msg_headerlen - len(buf))
                if not newbuf:
                    return msgs
                buf += newbuf
            datalen, msgid = struct.unpack(msg_fmtstring, buf[:msg_headerlen])
            data = buf[msg_headerlen:]
            while datalen > len(data):
                newdata = sock.recv(1024)
                if not newdata:
                    return msgs
                data += newdata
            msg = msgids[msgid]()
            buf = data[datalen:]
            data = data[:datalen]
            msg.proto.ParseFromString(data)
            msgs.append(msg)
            if not buf:
                return msgs
        except socket.error as e:
            print e
            raise e

def buildPacket(msg):
    data = msg.proto.SerializeToString()
    headerdata = struct.pack(msg_fmtstring, len(data), msg.msgid)
    return headerdata + data

def doSelect(readsockets, readfunc, exceptfunc, timeout = None):
    readsocks, w, exceptsocks = select.select(readsockets, [], readsockets, timeout)
    for exceptsock in exceptsocks:
        exceptfunc(exceptsock)
    for readsock in readsocks:
        readfunc(readsock)

