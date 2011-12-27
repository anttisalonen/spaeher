#/usr/bin/env python2

import sys
import time
import socket

import message
import game
import ai
import fromClient, toClient

class Client:
    def __init__(self, name, server, configurator):
        self.connected = True
        self.ownedTeamIDs = []
        self.gameState = game.GameState()
        self.name = name
        self.server = server
        self.isConfigurator = configurator
        self.ownTeamID = 0 if configurator else 1
        self.clientid = self.ownTeamID
        self.ai = ai.AI(self.ownTeamID)

    def sendMessage(self, message):
        # TODO
        self.send(message)

    def send(self, msg):
        parsed_msg = toClient.ParseFromString(msg.tid, toClient.SerializeToString(msg))
        parsed_msg.handleMessageForClient(self)

    def init(self):
        self.server.handleNewClient(self)
        if self.isConfigurator:
            self.server.handleClientData(self, fromClient.ServerConfiguration(game.GameConfiguration(40, 40)))
            self.server.handleClientData(self, fromClient.ChatMessage("I'll take the first team"))
        self.server.handleClientData(self, fromClient.GetTeam(self.ownTeamID))

    def startGame(self):
        self.server.handleClientData(self, fromClient.StartGame())

    def quitGame(self):
        self.server.handleClientExit(self)

    def play(self):
        while self.gameState and self.gameState.activeTeamID == self.ownTeamID:
            msg = self.ai.decide(self.gameState)
            self.server.handleClientData(self, msg)

class Sock_Client:
    def __init__(self, name, configurator):
        self.port = 32105
        self.name = name
        self.configurator = configurator
        self.ownTeamID = 0 if configurator else 1
        self.connected = False
        self.clientid = self.ownTeamID
        self.ai = ai.AI(self.ownTeamID)
        self.server_is_silent = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', self.port))
        self.sock.setblocking(0)
        self.connected = True
        self.inLobby = True
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        def selectExcept(exceptsock):
            print "Exception with socket", exceptsock
            exceptsock.close()
            if exceptsock is self.sock:
                raise IOError
            else:
                self.handle_disconnecting_client(exceptsock)

        def selectRead(readsock):
            self.server_is_silent = False
            msgs = message.recvMessage(readsock)
            if not msgs:
                self.sock.close()
                self.connected = False
                print "Disconnected from server"
            else:
                for msg in msgs:
                    print "Incoming server message:", msg
                    msg.handleMessageForClient(self)

        while self.connected:
            while True:
                self.server_is_silent = True
                message.doSelect([self.sock], selectRead, selectExcept, 0.1)
                if self.server_is_silent:
                    break;
            if not self.inLobby:
                if self.gameState.activeTeamID == self.ownTeamID:
                    msg = self.ai.decide(self.gameState)
                    self.send_to_server(msg)

    def send_to_server(self, msg):
        print "Sending to server:", msg
        self.sock.send(message.buildPacket(msg))

def main():
    name = "Client 2"
    if len(sys.argv) > 1:
        name = sys.argv[1]
    sock_client = Sock_Client(name, name == "Client 1")
    sock_client.connect()

if __name__ == '__main__':
    main()

