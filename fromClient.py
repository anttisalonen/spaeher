#/usr/bin/env python2

import game
import toClient
import Server

class ServerConfiguration:
    def __init__(self, config):
        self.configuration = config

    def handleLobbyEvent(self, lobby, client):
        lobby.server.setConfiguration(client, self.configuration)

class ChatMessage:
    def __init__(self, msg):
        self.msg = msg

    def handleLobbyEvent(self, lobby, client):
        lobby.server.broadcast(self)

    def handleGameEvent(self, game, client):
        game.server.broadcast(self)

    def handleMessageForClient(self, client):
        print client.name, "received:", self.msg

class GetTeam:
    def __init__(self, teamnumber):
        self.teamnumber = teamnumber

    def handleLobbyEvent(self, lobby, client):
        lobby.server.setTeamOwner(client, self.teamnumber)

class StartGame:
    def __init__(self):
        pass

    def handleLobbyEvent(self, lobby, client):
        if lobby.server.config:
            g = game.GameState()
            g.aps = 100
            getpos = lambda x, y: lobby.server.config.getInitialSoldierPosition(x, y)
            for x in xrange(lobby.server.config.numTeams):
                t = game.Team(x)
                t.generateSoldiers(lobby.server.config.numSoldiers[x], getpos)
                g.teams[t.teamID] = t
            g.activeTeamID = 0
            g.activeSoldierID = g.teams[g.activeTeamID].soldiers[0].soldierID
            g.battlefield = game.Battlefield(lobby.server.config.bfwidth, lobby.server.config.bfheight)
            lobby.server.setMode(Server.Game(lobby.server, g))
            lobby.server.broadcast(toClient.InitialGameData(g))

class EndOfTurnCommand:
    def __init__(self):
        pass

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientid, g.gameState.activeTeamID):
            g.endTurn()

class MoveForwardCommand:
    def __init__(self):
        pass

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientid, g.gameState.activeTeamID):
            g.moveForward()

class TurnCommand:
    def __init__(self, toright):
        self.toright = toright

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientid, g.gameState.activeTeamID):
            g.turn(self.toright)

class ShootCommand:
    def __init__(self, pos):
        self.pos = pos

    def handleGameEvent(self, g, client):
        if g.server.clientControls(client.clientid, g.gameState.activeTeamID):
            g.decrementAPs(20)
            sold = g.gameState.soldierOn(self.pos)
            if sold and sold.hps > 0:
                g.killSoldier(sold)
