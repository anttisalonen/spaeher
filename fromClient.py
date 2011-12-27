#/usr/bin/env python2

import game
import toClient
import Server
import creation

import proto.messages_pb2

class ChatMessage:
    msgid = 1001
    def __init__(self, msg = ''):
        self.proto = proto.messages_pb2.ChatMessage()
        self.proto.chatmsg = msg

    def handleLobbyEvent(self, lobby, client):
        lobby.server.broadcast(self)

    def handleGameEvent(self, game, client):
        game.server.broadcast(self)

    def handleMessageForClient(self, client):
        print client.name, "received:", self.proto.chatmsg

class ServerConfiguration:
    msgid = 1002
    def __init__(self, config = None):
        self.proto = proto.messages_pb2.ServerConfigurationMessage()
        if config:
            self.proto.bfheight = config.bfheight
            self.proto.bfwidth = config.bfwidth

    def handleLobbyEvent(self, lobby, client):
        lobby.server.setConfiguration(client, game.GameConfiguration(self.proto.bfheight, self.proto.bfwidth))

class StartGame:
    msgid = 1003
    def __init__(self):
        self.proto = proto.messages_pb2.StartGameMessage()

    def handleLobbyEvent(self, lobby, client):
        if lobby.server.config:
            g = creation.generateGameState(lobby.server.config)
            lobby.server.setMode(Server.Game(lobby.server, g))
            lobby.server.broadcast(toClient.InitialGameData(g))

class GetTeam:
    msgid = 1004
    def __init__(self, teamnumber = None):
        self.proto = proto.messages_pb2.GetTeamMessage()
        if teamnumber:
            self.proto.teamnumber = teamnumber

    def handleLobbyEvent(self, lobby, client):
        lobby.server.setTeamOwner(client, self.proto.teamnumber)

class EndOfTurnCommand:
    msgid = 1005
    def __init__(self):
        self.proto = proto.messages_pb2.EndOfTurnCommand()

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientID, g.gameState.activeTeamID):
            g.endTurn()
        else:
            print "Warning: client", client.clientID, "sends command when not allowed"

class MoveForwardCommand:
    msgid = 1006
    def __init__(self):
        self.proto = proto.messages_pb2.MoveForwardCommand()

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientID, g.gameState.activeTeamID):
            g.moveForward()
        else:
            print "Warning: client", client.clientID, "sends command when not allowed"

class TurnCommand:
    msgid = 1007
    def __init__(self, toright = False):
        self.proto = proto.messages_pb2.TurnCommand()
        self.proto.toright = toright

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientID, g.gameState.activeTeamID):
            g.turn(self.proto.toright)
        else:
            print "Warning: client", client.clientID, "sends command when not allowed"

class ShootCommand:
    msgid = 1008
    def __init__(self, pos = None):
        self.proto = proto.messages_pb2.ShootCommand()
        if pos:
            self.proto.pos.x = pos.x
            self.proto.pos.y = pos.y

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientID, g.gameState.activeTeamID):
            g.decrementAPs(20)
            pos = game.Position(self.proto.pos.x, self.proto.pos.y)
            sold = g.gameState.soldierOn(pos)
            if sold and sold.hps > 0 and game.vectorLength(game.subVectors(sold.position, g.gameState.getActiveSoldier().position)) < 10:
                g.killSoldier(sold)
        else:
            print "Warning: client", client.clientID, "sends command when not allowed"
