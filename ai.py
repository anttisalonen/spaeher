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
        self.tasks.append(ExploreTask(gameState, self.ownTeamID))

    def decide(self, gameState):
        msg = None
        while not msg:
            if len(self.tasks) == 0:
                self.updateTasks(gameState)
            msg = self.tasks[0].execute(gameState)
            if not msg:
                self.tasks.popleft()
        return msg

    def handleSoldierData(self, gameState, soldier):
        if soldier.teamID != self.ownTeamID and (len(self.tasks) == 0 or isinstance(self.tasks[0], ExploreTask)):
            print self.ownTeamID, "hunting for a soldier on", soldier.position
            self.tasks.appendleft(HuntTask(gameState, soldier, self.ownTeamID))

class HuntTask:
    def __init__(self, gameState, soldier, ownTeamID):
        self.target = soldier
        self.ownTeamID = ownTeamID

    def execute(self, gameState):
        print self.ownTeamID, "Executing hunt task"
        if self.target.teamID in gameState.teams and self.target.soldierID in gameState.teams[self.target.teamID].soldiers:
            self.target = gameState.teams[self.target.teamID].soldiers[self.target.soldierID]
        tgtvec = game.subVectors(self.target.position, gameState.getActiveSoldier().position)
        if game.vectorLength(tgtvec) < 10:
            sold = gameState.soldierOn(self.target.position)
            if sold and sold.teamID != self.ownTeamID:
                print self.ownTeamID, "shooting"
                return fromClient.ShootCommand(self.target.position)
            else:
                print self.ownTeamID, "giving up on hunt, no idea where he went"
                return None
        else:
            print self.ownTeamID, "hunting from", gameState.getActiveSoldier().position, "to", self.target.position
            return gotoCommand(tgtvec, gameState)

class ExploreTask:
    def __init__(self, gameState, ownTeamID):
        self.ownTeamID = ownTeamID
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

        print self.ownTeamID, "moving to", self.exploreTargets[0], "from", gameState.getActiveSoldier().position
        return gotoCommand(tgtvec, gameState)

def gotoCommand(tgtvec, gameState):
    nextdir = game.vectorToDirection(tgtvec)
    mydir = gameState.getActiveSoldier().direction 
    if mydir == nextdir:
        assert gameState.canMoveForward(), "AI: walking to a wall"
        return fromClient.MoveForwardCommand()
    else:
        if mydir < nextdir:
            return fromClient.TurnCommand(True)
        else:
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
