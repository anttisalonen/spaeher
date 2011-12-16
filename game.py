#/usr/bin/env python2

import math

import toClient
import message

class GameState:
    def __init__(self):
        self.teams = {}

    def setSoldier(self, soldier):
        if soldier.teamID not in self.teams:
            self.teams[soldier.teamID] = Team(soldier.teamID)
        self.teams[soldier.teamID].soldiers[soldier.soldierID] = soldier

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
        self.numSoldiers = [4] * self.numTeams

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
            position = getpos(self.teamID, x + 1)
            self.soldiers.append(Soldier(x, self.teamID, position))

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

def addVectors(v1, v2):
    return Position(v1.x + v2.x, v1.y + v2.y)

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
        xdiff = abs(pos1.x - pos2.x)
        ydiff = abs(pos1.y - pos2.y)
        if xdiff < 20:
            return False
        if ydiff < 20:
            return False
        return math.sqrt(ydiff * ydiff + xdiff * xdiff) < 20

class Direction:
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7

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
        if self.direction == Direction.N:
            self.movementVector = Position(0, 1)
        elif self.direction == Direction.NE:
            self.movementVector = Position(1, 1)
        elif self.direction == Direction.E:
            self.movementVector = Position(1, 0)
        elif self.direction == Direction.SE:
            self.movementVector = Position(1, -1)
        elif self.direction == Direction.S:
            self.movementVector = Position(0, -1)
        elif self.direction == Direction.SW:
            self.movementVector = Position(-1, -1)
        elif self.direction == Direction.W:
            self.movementVector = Position(-1, 0)
        elif self.direction == Direction.NW:
            self.movementVector = Position(-1, 1)

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

