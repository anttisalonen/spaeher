#/usr/bin/env python2

from copy import deepcopy

import fromClient
import game

import proto.messages_pb2

import google.protobuf.message

class GreetingMessage:
    msgid = 1
    def __init__(self, msg = ""):
        self.proto = proto.messages_pb2.GreetingMessage()
        self.proto.greetingmsg = msg

    def handleMessageForClient(self, client):
        print client.name, "received server greeting:", self.proto.greetingmsg
        client.send_to_server(fromClient.GetTeam(client.ownTeamID))
        if client.configurator:
            client.send_to_server(fromClient.ServerConfiguration(game.GameConfiguration(40, 40)))
            client.send_to_server(fromClient.ChatMessage("I'll take the first team"))
            client.send_to_server(fromClient.StartGame())

class InitialGameData:
    msgid = 2
    def __init__(self, g = None):
        self.proto = proto.messages_pb2.InitialGameDataMessage()
        if g:
            self.gameToProtoGame(g)

    def handleMessageForClient(self, client):
        client.inLobby = False
        client.gameState = self.protoGameToGame()

    def gameToProtoGame(self, g):
        self.proto.game.turnNumber = g.turnNumber
        self.proto.game.activeTeamID = g.activeTeamID
        self.proto.game.activeSoldierID = g.activeSoldierID
        for team in g.teams.values():
            t = self.proto.game.teams.add()
            t.teamID = team.teamID
            for soldier in team.soldiers.values():
                s = t.soldiers.add()
                soldierToProtoSoldier(soldier, s)
        self.proto.game.battlefield.width = g.battlefield.width
        self.proto.game.battlefield.height = g.battlefield.height
        for row in g.battlefield.array:
            for col in row:
                t = self.proto.game.battlefield.tiles.add()
                t.tile = col

    def protoGameToGame(self):
        g = game.GameState()
        for team in self.proto.game.teams:
            t = game.Team(team.teamID)
            g.teams[team.teamID] = t
            for soldier in team.soldiers:
                t.soldiers[soldier.soldierID] = protoSoldierToSoldier(soldier)
        g.turnNumber = self.proto.game.turnNumber
        g.activeTeamID = self.proto.game.activeTeamID
        g.activeSoldierID = self.proto.game.activeSoldierID
        g.battlefield = game.Battlefield(self.proto.game.battlefield.width, self.proto.game.battlefield.height)
        for x, t in enumerate(self.proto.game.battlefield.tiles):
            g.battlefield.array[x // self.proto.game.battlefield.height][x % self.proto.game.battlefield.width] = t.tile
        return g

def soldierToProtoSoldier(soldier, ps):
    ps.soldierID = soldier.soldierID
    ps.teamID = soldier.teamID
    ps.position.x = soldier.position.x
    ps.position.y = soldier.position.y
    ps.direction = soldier.direction
    ps.hps = soldier.hps

def protoSoldierToSoldier(soldier):
    pos = game.Position(soldier.position.x, soldier.position.y)
    s = game.Soldier(soldier.teamID, soldier.soldierID, pos)
    s.direction = soldier.direction
    s.hps = soldier.hps
    return s

class TurnData:
    msgid = 3
    def __init__(self, activeteamid = None, activesoldierid = None, aps = None):
        self.proto = proto.messages_pb2.TurnDataMessage()
        if activeteamid:
            self.proto.activeTeamID = activeteamid
        if activesoldierid:
            self.proto.activeSoldierID = activesoldierid
        if aps:
            self.proto.aps = aps

    def handleMessageForClient(self, client):
        client.gameState.activeTeamID = self.proto.activeTeamID
        client.gameState.activeSoldierID = self.proto.activeSoldierID
        client.gameState.aps = self.proto.aps

    def __str__(self):
        return "<%s> Team %d, Soldier %d, APs %d" % (self.__class__.__name__, self.proto.activeTeamID, self.proto.activeSoldierID, self.proto.aps)

class SoldierData:
    msgid = 4
    def __init__(self, soldier = None):
        self.proto = proto.messages_pb2.SoldierDataMessage()
        if soldier:
            soldierToProtoSoldier(soldier, self.proto.soldier)

    def handleMessageForClient(self, client):
        sold = protoSoldierToSoldier(self.proto.soldier)
        if sold.hps <= 0:
            client.gameState.removeSoldier(sold.teamID, sold.soldierID)
        else:
            client.gameState.setSoldier(sold)
            client.ai.handleSoldierData(client.gameState, sold)

    def __str__(self):
        return "<%s> Team %d, Soldier %d, HPs %d, Position (%d, %d), Direction %d" % (self.__class__.__name__, self.proto.soldier.teamID, self.proto.soldier.soldierID, self.proto.soldier.hps, self.proto.soldier.position.x, self.proto.soldier.position.y, self.proto.soldier.direction)

class RemoveSoldierData:
    msgid = 5
    def __init__(self, teamid = None, soldierid = None):
        self.proto = proto.messages_pb2.RemoveSoldierDataMessage()
        if teamid:
            self.proto.teamID = teamid
        if soldierid:
            self.proto.soldierID = soldierid

    def handleMessageForClient(self, client):
        client.gameState.removeSoldier(self.proto.teamID, self.proto.soldierID)

    def __str__(self):
        return "<%s> Team %d, Soldier %d" % (self.__class__.__name__, self.proto.teamID, self.proto.soldierID)

class SoldierAPData:
    msgid = 6
    def __init__(self, aps = None):
        self.proto = proto.messages_pb2.SoldierAPDataMessage()
        if aps:
            self.proto.aps = aps

    def handleMessageForClient(self, client):
        client.gameState.aps = self.proto.aps

    def __str__(self):
        return "<%s> APs %d" % (self.__class__.__name__, self.proto.aps)

class GameOverData:
    msgid = 7
    def __init__(self, winningTeamID = None):
        self.proto = proto.messages_pb2.GameOverDataMessage()
        if winningTeamID:
            self.proto.winningTeamID = winningTeamID

    def handleMessageForClient(self, client):
        client.gameState = None
        client.inLobby = True
        print client.name, "Game over - winning team:", self.proto.winningTeamID

