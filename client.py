#/usr/bin/env python2

import time

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
        msg.handleMessageForClient(self)

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
        while self.gameState.activeTeamID == self.ownTeamID:
            msg = self.ai.decide(self.gameState)
            self.server.handleClientData(self, msg)

