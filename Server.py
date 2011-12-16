#/usr/bin/env python2

from copy import deepcopy
import os

import client
import fromClient, toClient
import game
import message

class Game:
    def __init__(self, server, gamestate):
        self.server = server
        self.gameState = gamestate

    def handleNewClient(self, client):
        print "Not accepting new client during play"

    def handleClientData(self, client, data):
        event = message.getClientData(data)
        if event:
            if hasattr(event, "handleGameEvent"):
                event.handleGameEvent(self, client)
            else:
                print "Invalid data from client"

    def handleClientExit(self, client):
        print "Client quit"

    def endTurn(self):
        self.gameState.activeTeamID += 1
        if self.gameState.activeTeamID >= len(self.gameState.teams):
            self.gameState.activeTeamID = 0
        self.gameState.aps = 100
        self.gameState.activeSoldierID = self.gameState.teams[self.gameState.activeTeamID].soldiers[0].soldierID
        self.checkGameOver()
        self.updateClientTurnState()

    def moveForward(self):
        newpos = self.gameState.canMoveForward()
        if newpos:
            self.gameState.getActiveSoldier().position = newpos
            self.updateClientSoldierState()
            self.decrementAPs()

    def turn(self, toright):
        if self.gameState.aps > 0:
            self.gameState.getActiveSoldier().turn(toright)
            self.updateClientSoldierState()

    def decrementAPs(self):
        self.gameState.aps -= 10
        self.updateClientAPState()
        if self.gameState.aps <= 0:
            self.endTurn()

    def updateClientAPState(self):
        self.server.broadcast(toClient.SoldierAPData(self.gameState.aps))

    def updateClientSoldierState(self):
        soldier = self.gameState.getActiveSoldier()
        for team in self.gameState.teams.values():
            for soldier2 in team.soldiers:
                if team.teamID == self.gameState.activeTeamID or self.gameState.battlefield.visibleFrom(soldier2.position, soldier.position):
                    self.server.sendData(team.teamID, toClient.SoldierData(soldier))

    def updateClientTurnState(self):
        self.server.broadcast(toClient.TurnData(self.gameState.activeTeamID, self.gameState.activeSoldierID))

    def checkGameOver(self):
        for team in self.gameState.teams.values():
            if team.dead():
                self.server.setMode(Lobby(self.server))
                return True
        return False

class Lobby:
    def __init__(self, server):
        self.server = server

    def handleNewClient(self, client):
        self.sendGreeting(client)

    def handleClientData(self, client, data):
        event = message.getClientData(data)
        self.debugging = True
        if event:
            if self.debugging:
                event.handleLobbyEvent(self, client)
            else:
                try:
                    event.handleLobbyEvent(self, client)
                except AttributeError:
                    print "Unknown data from client"
        else:
            print "Unknown data from client"

    def handleClientExit(self, client):
        print "Lobby: Client quit"

    def sendGreeting(self, client):
        client.sendMessage(toClient.GreetingMessage("Hello!"))

class Lock:
    def __init__(self):
        self.locked = False

    def __enter__(self):
        if self.locked:
            raise AttributeError("The lock is held! What are the threading primitives in Python!")
        self.locked = True

    def __exit__(self, p1, p2, p3):
        self.locked = False

class Server:
    def __init__(self):
        self.mode = Lobby(self)
        self.lock = Lock()
        self.clients = []
        self.config = None
        self.teamowners = {}

    def setConfiguration(self, client, config):
        with self.lock:
            self.config = config

    def setMode(self, mode):
        with self.lock:
            self.mode = mode

    def broadcast(self, message):
        with self.lock:
            for client in self.clients:
                client.sendMessage(message)

    def sendData(self, teamID, msg):
        if teamID in self.teamowners:
            self.clients[self.teamowners[teamID]].sendMessage(msg)

    def setTeamOwner(self, client, teamnumber):
        with self.lock:
            if teamnumber not in self.teamowners or not self.teamowners[teamnumber].connected:
                self.teamowners[teamnumber] = client.clientid
                client.ownedTeamIDs.append(teamnumber)

    def handleNewClient(self, client):
        self.mode.handleNewClient(client)
        self.clients.append(client)

    def handleClientData(self, client, data):
        self.mode.handleClientData(client, data)

    def handleClientExit(self, client):
        self.clients.remove(client)
        self.mode.handleClientExit(client)

    def gameOn(self):
        with self.lock:
            return isinstance(self.mode, Game)

    def clientControls(self, clientid, teamID):
        return teamID in self.teamowners and clientid == self.teamowners[teamID]

    def controllingClientID(self, teamID):
        if teamID in self.teamowners:
            return self.teamowners[teamID]
        else:
            return None