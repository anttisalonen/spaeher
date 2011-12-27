#/usr/bin/env python2

from copy import deepcopy
import os
import socket
import select

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

    def handleClientMessage(self, client, msg):
        if hasattr(msg, "handleGameEvent"):
            msg.handleGameEvent(self, client)
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

    def handleClientMessage(self, client, msg):
        self.debugging = True
        if self.debugging:
            msg.handleLobbyEvent(self, client)
        else:
            try:
                msg.handleLobbyEvent(self, client)
            except AttributeError:
                print "Unknown data from client"

    def handleClientExit(self, client):
        print "Lobby: Client quit"

    def sendGreeting(self, client):
        client.sendMessage(toClient.GreetingMessage("Hello!"))

class Server:
    def __init__(self):
        self.mode = Lobby(self)
        self.clients = dict()
        self.config = None
        self.teamowners = dict()

    def setConfiguration(self, client, config):
        self.config = config

    def setMode(self, mode):
        self.mode = mode

    def broadcast(self, message):
        for client in self.clients.values():
            client.sendMessage(message)

    def sendData(self, teamID, msg):
        if teamID in self.teamowners:
            self.clients[self.teamowners[teamID]].sendMessage(msg)

    def setTeamOwner(self, client, teamnumber):
        if teamnumber not in self.teamowners:
            self.teamowners[teamnumber] = client.clientID
            client.ownedTeamIDs.append(teamnumber)

    def handleNewClient(self, client):
        self.mode.handleNewClient(client)
        self.clients[client.clientID] = client

    def handleClientMessage(self, client, msg):
        self.mode.handleClientMessage(client, msg)

    def handleClientExit(self, client):
        del self.clients[client.clientID]
        for teamID, cl in self.teamowners.items():
            if cl == client.clientID:
                del self.teamowners[teamID]
        self.mode.handleClientExit(client)
        if not self.clients and not isinstance(self.mode, Lobby):
            print "No more clients - back to lobby"
            self.mode = Lobby(self)

    def gameOn(self):
        return isinstance(self.mode, Game)

    def clientControls(self, clientid, teamID):
        return teamID in self.teamowners and clientid == self.teamowners[teamID]

    def controllingClientID(self, teamID):
        if teamID in self.teamowners:
            return self.teamowners[teamID]
        else:
            return None

class Sock_Server:
    def __init__(self):
        self.port = 32105
        self.nextClientID = 1

    class Sock_Client:
        def __init__(self, sock, clientID):
            self.sock = sock
            self.clientID = clientID
            self.ownedTeamIDs = []

        def sendMessage(self, msg):
            print "Sending to client:", msg
            self.sock.send(message.buildPacket(msg))

    def serve(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.sock.bind(('', self.port))
        self.sock.listen(10)
        self.clientsockets = dict()
        self.gameserver = Server()
        self.loop()

    def loop(self):
        def selectExcept(exceptsock):
            print "Exception with socket", exceptsock
            exceptsock.close()
            if exceptsock is self.sock:
                raise IOError
            else:
                self.handle_disconnecting_client(exceptsock)

        def selectRead(readsock):
            if readsock is self.sock:
                self.do_accept()
            else:
                self.handle_incoming_client_data(readsock)

        while True:
            message.doSelect([self.sock] + self.clientsockets.keys(), selectRead, selectExcept)

    def do_accept(self):
        print "Accepting connection"
        conn, addr = self.sock.accept()
        conn.setblocking(0)
        cl = self.Sock_Client(conn, self.nextClientID)
        self.nextClientID += 1
        self.clientsockets[conn] = cl
        self.gameserver.handleNewClient(cl)

    def handle_incoming_client_data(self, clientsock):
        msgs = message.recvMessage(clientsock)
        if not msgs:
            self.handle_disconnecting_client(clientsock)
        else:
            for msg in msgs:
                print "Incoming client message:", msg
                self.gameserver.handleClientMessage(self.clientsockets[clientsock], msg)

    def handle_disconnecting_client(self, clientsock):
        print "Client disconnected"
        self.gameserver.handleClientExit(self.clientsockets[clientsock])
        del self.clientsockets[clientsock]

def main():
    sock_server = Sock_Server()
    sock_server.serve()

if __name__ == '__main__':
    main()

