#/usr/bin/env python2

import random

import game

def generateGameState(config):
    random.seed(21)
    g = game.GameState(100)
    getpos = lambda x, y: config.getInitialSoldierPosition(x, y)
    for x in xrange(config.numTeams):
        t = game.Team(x)
        t.generateSoldiers(config.numSoldiers[x], getpos)
        g.teams[t.teamID] = t
    g.activeSoldierID = g.teams[g.activeTeamID].soldiers[0].soldierID

    g.battlefield = game.Battlefield(config.bfwidth, config.bfheight)
    for x in xrange(g.battlefield.width):
        for y in xrange(g.battlefield.height):
            g.battlefield.array[x][y] = random.randint(game.Tile.grass, game.Tile.tree)

    return g
