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
        self.teamIDs = self.gameState.teams.keys()
        self.soldierIDs = dict()
        self.currentSoldierIDs = dict()
        for teamid in self.teamIDs:
            self.soldierIDs[teamid] = self.gameState.teams[teamid].soldiers.keys()
            self.currentSoldierIDs[teamid] = 0
        self.currentTeamIDIndex = 0

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

    def incrementCurrentTeamID(self):
        self.currentTeamIDIndex += 1
        if self.currentTeamIDIndex >= len(self.teamIDs):
            self.currentTeamIDIndex = 0

    def incrementCurrentSoldierID(self):
        team = self.gameState.teams[self.teamIDs[self.currentTeamIDIndex]]
        increments = 0
        while True:
            self.currentSoldierIDs[team.teamID] += 1
            increments += 1
            if self.currentSoldierIDs[team.teamID] >= len(team.soldiers):
                self.currentSoldierIDs[team.teamID] = 0
            if not team.soldiers[self.currentSoldierIDs[team.teamID]].dead():
                break
            elif increments > len(team.soldiers):
                raise ValueError, "Tried finding alive soldier, but they're all dead"

    def updateCurrentTeamID(self):
        self.incrementCurrentTeamID()
        increments = 1
        while self.gameState.teams[self.teamIDs[self.currentTeamIDIndex]].dead():
            self.incrementCurrentTeamID()
            increments += 1
            if increments >= len(self.teamIDs):
                self.currentTeamIDIndex = -1
                return
        self.incrementCurrentSoldierID()

    def endTurn(self):
        print "End turn"
        self.updateCurrentTeamID()
        if self.currentTeamIDIndex == -1:
            # Game over
            print "Game over"
            self.sendGameOverToClients(self.gameState.activeTeamID)
            self.server.setMode(Lobby(self.server))
        else:
            newteamid = self.teamIDs[self.currentTeamIDIndex]
            self.gameState.nextTurn(newteamid, self.currentSoldierIDs[newteamid])
            self.updateClientTurnState()

    def moveForward(self):
        newpos = self.gameState.canMoveForward()
        if newpos and self.decrementAPs(10):
            self.gameState.getActiveSoldier().position = newpos
            self.updateClientSoldierState(self.gameState.getActiveSoldier())

    def turn(self, toright):
        if self.decrementAPs(1):
            self.gameState.getActiveSoldier().turn(toright)
            self.updateClientSoldierState(self.gameState.getActiveSoldier())

    def killSoldier(self, soldier):
        self.gameState.killSoldier(soldier)
        self.updateClientSoldierState(soldier)
        print "Soldier from team", soldier.teamID, "killed"

    def decrementAPs(self, num):
        if self.gameState.aps >= num:
            self.gameState.aps -= num
            self.updateClientAPState()
            return True
        else:
            return False

    def updateClientAPState(self):
        self.server.broadcast(toClient.SoldierAPData(self.gameState.aps))

    def updateClientSoldierState(self, soldier):
        for team in self.gameState.teams.values():
            if team.teamID == soldier.teamID:
                self.server.sendData(team.teamID, toClient.SoldierData(soldier))
            else:
                visibleToTeam = False
                for soldier2 in team.soldiers.values():
                    # check if the moving soldier is seen
                    if self.gameState.battlefield.visibleFrom(soldier2.position, soldier.position):
                        self.server.sendData(team.teamID, toClient.SoldierData(soldier))
                        visibleToTeam = True
                    # check if the moving soldier sees
                    if self.gameState.battlefield.visibleFrom(soldier.position, soldier2.position):
                        self.server.sendData(soldier.teamID, toClient.SoldierData(soldier2))
                if not visibleToTeam:
                    self.server.sendData(team.teamID, toClient.RemoveSoldierData(soldier.teamID, soldier.soldierID))

    def updateClientTurnState(self):
        self.server.broadcast(toClient.TurnData(self.gameState.activeTeamID, self.gameState.activeSoldierID, self.gameState.aps))

    def sendGameOverToClients(self, winningTeamID):
        self.server.broadcast(toClient.GameOverData(winningTeamID))

    def checkGameOver(self):
        for team in self.gameState.teams.values():
            if team.dead():
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
