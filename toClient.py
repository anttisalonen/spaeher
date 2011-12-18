#/usr/bin/env python2

from copy import deepcopy

class GreetingMessage:
    def __init__(self, msg):
        self.msg = msg

    def handleMessageForClient(self, client):
        print client.name, "received server greeting:", self.msg

class InitialGameData:
    def __init__(self, game):
        self.game = game

    def handleMessageForClient(self, client):
        client.gameState = deepcopy(self.game)

class SoldierData:
    def __init__(self, soldier):
        self.soldier = soldier

    def handleMessageForClient(self, client):
        client.gameState.setSoldier(self.soldier)
        client.ai.handleSoldierData(client.gameState, self.soldier)

class RemoveSoldierData:
    def __init__(self, teamid, soldierid):
        self.teamID = teamid
        self.soldierID = soldierid

    def handleMessageForClient(self, client):
        client.gameState.removeSoldier(self.teamID, self.soldierID)

class SoldierAPData:
    def __init__(self, aps):
        self.aps = aps

    def handleMessageForClient(self, client):
        client.gameState.aps = self.aps

class TurnData:
    def __init__(self, activeteamid, activesoldierid, aps):
        self.activeteamid = activeteamid
        self.activesoldierid = activesoldierid
        self.aps = aps

    def handleMessageForClient(self, client):
        client.gameState.activeTeamID = self.activeteamid
        client.gameState.activeSoldierID = self.activesoldierid
        client.gameState.aps = self.aps
