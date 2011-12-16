#/usr/bin/env python2

import Queue
import fromClient

class AI:
    def __init__(self, ownTeamID):
        self.ownTeamID = ownTeamID
        self.whereToGo = Queue.Queue()

    def decide(self, gameState):
        if gameState.canMoveForward():
            print self.ownTeamID, "moving"
            return fromClient.MoveForwardCommand()
        else:
            print self.ownTeamID, "turning"
            return fromClient.TurnCommand(True)


