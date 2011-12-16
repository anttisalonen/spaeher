#/usr/bin/env python2

from copy import deepcopy
from collections import deque

import game
import fromClient

class AI:
    def __init__(self, ownTeamID):
        self.ownTeamID = ownTeamID
        self.tasks = deque()

    def updateTasks(self, gameState):
        print "AI updating tasks"
        self.tasks.append(ExploreTask(gameState))

    def decide(self, gameState):
        msg = None
        while not msg:
            if len(self.tasks) == 0:
                self.updateTasks(gameState)
            msg = self.tasks[0].execute(gameState)
            if not msg:
                self.tasks.popleft()
        return msg

class ExploreTask:
    def __init__(self, gameState):
        self.exploreTargets = deque()
        for i in xrange(0, gameState.battlefield.width - 1, 5):
            for j in xrange(0, gameState.battlefield.height - 1, 5):
                self.exploreTargets.append(game.Position(i, j))

    def execute(self, gameState):
        if len(self.exploreTargets) == 0:
            return None

        tgtvec = game.subVectors(self.exploreTargets[0], gameState.getActiveSoldier().position)
        if game.vectorLength(tgtvec) < 5:
            self.exploreTargets.popleft()
            if len(self.exploreTargets) == 0:
                return None
        nextdir = game.vectorToDirection(tgtvec)
        mydir = gameState.getActiveSoldier().direction 
        if mydir == nextdir:
            print "moving to", self.exploreTargets[0], "from", gameState.getActiveSoldier().position
            assert gameState.canMoveForward(), "AI: walking to a wall"
            return fromClient.MoveForwardCommand()
        else:
            if mydir < nextdir:
                print "turning right"
                return fromClient.TurnCommand(True)
            else:
                print "turning left"
                return fromClient.TurnCommand(False)

def getPath(p1, p2):
    # TODO: replace with bresenham, or something...
    pcursor = deepcopy(p1)
    path = []
    while pcursor != p2:
        if pcursor.x < p2.x:
            pcursor.x += 1
        elif pcursor.x > p2.x:
            pcursor.x -= 1
        if pcursor.y < p2.y:
            pcursor.y += 1
        elif pcursor.y > p2.y:
            pcursor.y -= 1
        path.append(deepcopy(pcursor))
    return path
