#/usr/bin/env python2

import Server
import client
import game

def serve(server):
    # TODO: replace with actual server
    cl1 = client.Client("Client 1", server, True)
    cl1.init()
    cl2 = client.Client("Client 2", server, False)
    cl2.init()
    cl1.startGame()
    assert hasattr(cl2, "gameState"), "client has no game state"
    while server.gameOn():
        cl1.play()
        cl2.play()
    cl1.quitGame()
    cl2.quitGame()

def main():
    s = Server.Server()
    serve(s)

if __name__ == '__main__':
    main()

