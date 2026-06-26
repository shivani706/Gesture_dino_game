class GestureController:
    def __init__(self, game):
        self.game = game

    def handle(self, gesture):
        if gesture == "JUMP":
            self.game.dino.jump()
        elif gesture == "BEND":
            self.game.dino.duck(True)
        else:
            self.game.dino.duck(False)