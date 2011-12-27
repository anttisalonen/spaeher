#/usr/bin/env python2

from copy import deepcopy
from collections import deque

import game
import fromClient

class AI:
    def __init__(self, ownTeamID):
        self.ownTeamID = ownTeamID
        self.tasks = dict()

    def updateTasks(self, gameState):
        print self.ownTeamID, gameState.activeSoldierID, "AI updating tasks"
        self.tasks[gameState.activeSoldierID] = deque()
        self.tasks[gameState.activeSoldierID].append(ExploreTask(gameState, self.ownTeamID))

    def decide(self, gameState):
        if gameState.aps < 10:
            return fromClient.EndOfTurnCommand()
        msg = None
        while not msg:
            if self.currentSoldierIdle(gameState):
                self.updateTasks(gameState)
            msg = self.tasks[gameState.activeSoldierID][0].execute(gameState)
            if not msg:
                self.tasks[gameState.activeSoldierID].popleft()
        return msg

    def currentSoldierIdle(self, gameState):
        return self.soldierIdle(gameState.activeSoldierID)

    def soldierIdle(self, soldierid):
        return soldierid not in self.tasks or len(self.tasks[soldierid]) == 0

    def handleSoldierData(self, gameState, soldier):
        if soldier.teamID != self.ownTeamID:
            for ownsoldier in gameState.teams[self.ownTeamID].soldiers.values():
                if self.soldierIdle(ownsoldier.soldierID) or isinstance(self.tasks[ownsoldier.soldierID][0], ExploreTask):
                    print self.ownTeamID, ownsoldier.soldierID, "hunting for a soldier on", soldier.position
                    self.tasks[ownsoldier.soldierID].clear()
                    self.tasks[ownsoldier.soldierID].appendleft(HuntTask(gameState, soldier, self.ownTeamID))
                else:
                    t = self.tasks[ownsoldier.soldierID][0]
                    if isinstance(t, HuntTask) and t.target.soldierID == soldier.soldierID and \
                        t.target.teamID == soldier.teamID and t.target.position != soldier.position:
                        print self.ownTeamID, ownsoldier.soldierID, "updating hunt position for a soldier on", soldier.position
                        self.tasks[ownsoldier.soldierID][0] = HuntTask(gameState, soldier, self.ownTeamID)

class HuntTask:
    def __init__(self, gameState, soldier, ownTeamID):
        self.target = soldier
        self.ownTeamID = ownTeamID
        self.path = None
        self.shot = False

    def execute(self, gameState):
        if self.shot:
            return None
        if not self.path:
            self.path = battlefield_bfs(gameState.battlefield, gameState.getActiveSoldier().position, self.target.position)
        if not self.path:
            return None
        if gameState.getActiveSoldier().position == self.path[0]:
            self.path.popleft()
            if not self.path:
                self.path = battlefield_bfs(gameState.battlefield, gameState.getActiveSoldier().position, self.target.position)
            if not self.path:
                return None
        tgtvec = game.subVectors(self.path[0], gameState.getActiveSoldier().position)
        if game.vectorLength(game.subVectors(self.target.position, gameState.getActiveSoldier().position)) < 10:
            sold = gameState.soldierOn(self.target.position)
            if sold and sold.teamID != self.ownTeamID:
                print self.ownTeamID, gameState.activeSoldierID, "shooting"
                self.shot = True
                return fromClient.ShootCommand(self.target.position)
            else:
                print self.ownTeamID, gameState.activeSoldierID, "giving up on hunt, no idea where he went"
                return None
        else:
            return gotoCommand(str(self.ownTeamID) + " " + str(gameState.activeSoldierID) + ": hunting from " + str(self.path[0]) + " to " + str(self.target.position), tgtvec, gameState)

def battlefield_bfs(bf, frompos, topos):
    return bfs(frompos, topos, lambda p: getBattlefieldNeighbours(bf, p))

class ExploreTask:
    def __init__(self, gameState, ownTeamID):
        self.ownTeamID = ownTeamID
        self.path = None
        self.exploreTargets = deque()
        for i in xrange(0, gameState.battlefield.width - 1, 5):
            for j in xrange(0, gameState.battlefield.height - 1, 5):
                pos = game.Position(i, j)
                if gameState.battlefield.spotFree(pos):
                    self.exploreTargets.append(pos)

    def execute(self, gameState):
        if len(self.exploreTargets) == 0:
            return None

        if self.path and gameState.getActiveSoldier().position == self.path[0]:
            self.path.popleft()

        while True:
            if self.path and gameState.battlefield.spotFree(self.path[0]):
                tgtvec = game.subVectors(self.path[0], gameState.getActiveSoldier().position)
                break
            while self.exploreTargets and \
                    game.vectorLength(game.subVectors(gameState.getActiveSoldier().position, self.exploreTargets[0])) < 2:
                self.exploreTargets.popleft()
            if not self.exploreTargets:
                return None
            self.path = battlefield_bfs(gameState.battlefield, gameState.getActiveSoldier().position, self.exploreTargets[0])
            if not self.path:
                self.exploreTargets.popleft()
                self.path = None
            else:
                self.path.popleft()

        return gotoCommand(str(self.ownTeamID) + " " + str(gameState.activeSoldierID) + ": exploring from " + str(gameState.getActiveSoldier().position) + " for " + str(self.exploreTargets[0]), tgtvec, gameState)

def getBattlefieldNeighbours(battlefield, pos):
    for n in game.gridneighbours(pos):
        if battlefield.spotFree(n):
            yield n

def gotoCommand(debstr, tgtvec, gameState):
    nextdir = game.vectorToDirection(tgtvec)
    mydir = gameState.getActiveSoldier().direction 
    if mydir == nextdir:
        print debstr
        # TODO: find out why this assertion fails
        #assert gameState.canMoveForward(), "AI: walking to a wall"
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

def bfs(frompos, topos, getneighbours):
    openposs = deque()
    closedposs = dict()
    thispos = frompos
    found = False
    print "path from", frompos, "to", topos
    closedposs[thispos] = None
    while True:
        if thispos == topos:
            found = True
            break
        neighbours = getneighbours(thispos)
        for neighbour in neighbours:
            if neighbour not in closedposs:
                openposs.append(neighbour)
                closedposs[neighbour] = thispos
        if not openposs:
            break
        else:
            thispos = openposs.popleft()
    if not found:
        return None
    else:
        path = deque()
        while thispos:
            path.appendleft(thispos)
            thispos = closedposs[thispos]
        return path
