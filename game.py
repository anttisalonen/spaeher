#/usr/bin/env python2

import math

import toClient
import message

class GameState:
    def __init__(self):
        self.teams = {}
        self.turnNumber = 0

    def setSoldier(self, soldier):
        if soldier.teamID not in self.teams:
            self.teams[soldier.teamID] = Team(soldier.teamID)
        self.teams[soldier.teamID].soldiers[soldier.soldierID] = soldier

    def nextTurn(self):
        self.activeTeamID += 1
        if self.activeTeamID >= len(self.teams):
            self.activeTeamID = 0
        self.aps = 100
        self.activeSoldierID = self.teams[self.activeTeamID].soldiers[0].soldierID
        self.turnNumber += 1

    def canMoveForward(self):
        activeSoldier = self.getActiveSoldier()
        newpos = addVectors(activeSoldier.position, activeSoldier.movementVector)
        if self.battlefield.spotFree(newpos) and self.aps >= 10:
            return newpos
        else:
            return None

    def getActiveSoldier(self):
        return self.teams[self.activeTeamID].soldiers[self.activeSoldierID]

class GameConfiguration:
    def __init__(self, bfwidth, bfheight):
        self.bfwidth = bfwidth
        self.bfheight = bfheight
        self.numTeams = 2
        self.numSoldiers = [1] * self.numTeams

    def getInitialSoldierPosition(self, teamID, soldierID):
        if teamID == 0:
            x = 0
        else:
            x = self.bfwidth - 1
        return Position(x, self.bfheight // 2)

class Team:
    def __init__(self, teamID):
        self.teamID = teamID
        self.soldiers = []

    def generateSoldiers(self, numsoldiers, getpos):
        for x in xrange(numsoldiers):
            position = getpos(self.teamID, x)
            self.soldiers.append(Soldier(self.teamID, x, position))

    def dead(self):
        return all([soldier.dead() for soldier in self.soldiers])

class Tile:
    grass = 0
    tree = 1

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def add(self, vec):
        self.x += vec.x
        self.y += vec.y

    def __str__(self):
        return str((self.x, self.y))

    def __eq__(self, p):
        return self.x == p.x and self.y == p.y

def addVectors(v1, v2):
    return Position(v1.x + v2.x, v1.y + v2.y)

def subVectors(v1, v2):
    return Position(v1.x - v2.x, v1.y - v2.y)

def vectorLength(v):
    return math.sqrt(v.x * v.x + v.y * v.y)

class Battlefield:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.array = [[]]
        for x in xrange(self.width):
            self.array.append([])
            for y in xrange(self.height):
                self.array[x].append(Tile.grass)

    def spotFree(self, pos):
        if pos.x < 0 or pos.y < 0 or pos.x >= self.width or pos.y >= self.height:
            return False
        return self.array[pos.x][pos.y] == 0

    def visibleFrom(self, pos1, pos2):
        # TODO: angle
        vl = vectorLength(subVectors(pos1, pos2))
        return vl < 20

class Direction:
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7

def directionToVector(direction):
    if direction == Direction.N:
        return Position(0, 1)
    elif direction == Direction.NE:
        return Position(1, 1)
    elif direction == Direction.E:
        return Position(1, 0)
    elif direction == Direction.SE:
        return Position(1, -1)
    elif direction == Direction.S:
        return Position(0, -1)
    elif direction == Direction.SW:
        return Position(-1, -1)
    elif direction == Direction.W:
        return Position(-1, 0)
    elif direction == Direction.NW:
        return Position(-1, 1)

def vectorToDirection(pos):
    if pos.x == 0 and pos.y > 0:
        return Direction.N
    elif pos.x > 0 and pos.y > 0:
        return Direction.NE
    elif pos.x > 0 and pos.y == 0:
        return Direction.E
    elif pos.x > 0 and pos.y < 0:
        return Direction.SE
    elif pos.x == 0 and pos.y < 0:
        return Direction.S
    elif pos.x < 0 and pos.y < 0:
        return Direction.SW
    elif pos.x < 0 and pos.y == 0:
        return Direction.W
    else:
        return Direction.NW

class Soldier:
    def __init__(self, teamID, soldierID, pos):
        self.teamID = teamID
        self.soldierID = soldierID
        self.position = pos
        self.direction = Direction.N
        self.updateMovementVector()
        self.hps = 100

    def dead(self):
        return self.hps <= 0

    def updateMovementVector(self):
        self.movementVector = directionToVector(self.direction)

    def turn(self, toright):
        if toright:
            if self.direction == Direction.NW:
                self.direction = Direction.N
            else:
                self.direction += 1
        else:
            if self.direction == Direction.N:
                self.direction = Direction.NW
            else:
                self.direction -= 1
        self.updateMovementVector()

