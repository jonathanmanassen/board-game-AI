import socket
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import protocol
from random import randrange
import random
import time
import copy

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
    game data
"""
# determines whether the power of the character is used before
# or after moving
permanents, two, before, after = {'pink'}, {
    'red', 'grey', 'blue'}, {'purple', 'brown'}, {'black', 'white'}
# reunion of sets
colors = before | permanents | after | two
# ways between rooms
passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]

# ways for the pink character
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9}, {
    4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5}, {7, 8, 4, 6}]

"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)

class Game:

    def __repr__(self):
        message = f"Tour: {self.num_tour},\n"
        message += f"Position Carlotta / exit: {self.position_carlotta}/{self.exit},\n"
        message += f"Shadow: {self.shadow},\n"
        message += f"blocked: {self.blocked}"
        message += "".join(["\n"+str(p) for p in self.characters])
        return message

    def set_game_state(self, game_state):
        
        self.game_state = {
            "position_carlotta": game_state['position_carlotta'],
            "exit": game_state['exit'],
            "num_tour": game_state['num_tour'],
            "shadow": game_state['shadow'],
            "blocked": game_state['blocked'],
            "characters": game_state['characters'],
            "active tiles": game_state['active tiles'],
        }
        self.game_state["fantom"] = game_state['fantom']
        self.fantom = next(x for x in self.game_state['characters'] if x['color'] == game_state['fantom'])

        self.x = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.nbSuspects = 0
        for char in self.game_state['characters']:
            if (char['suspect'] == True):
                self.nbSuspects += 1


        for char in self.game_state['characters']:
            self.x[char['position']] += 1

        self.heuriticScores = [0] * 10

        return self.game_state

    def change_character_position(self, character, position):
        self.x[character['position']] -= 1
        self.x[position] += 1
        next(x for x in self.game_state['characters'] if x['color'] == character['color'])['position'] = position
        character['position'] = position

    def heuristic(self):
        reveal = True
        if (self.x[self.fantom['position']] > 1 and self.fantom['position'] != self.game_state['shadow']):
            reveal = False

        number_revealed_suspects = 0
        for char in self.game_state['characters']:
            if (char == self.fantom or char['suspect'] == False):
                continue
            if (self.x[char['position']] > 1 and char['position'] != self.game_state['shadow'] and reveal == True):
                number_revealed_suspects += 1
            if ((self.x[char['position']] == 1 or char['position'] == self.game_state['shadow']) and reveal == False):
                number_revealed_suspects += 1

        score = (self.nbSuspects - number_revealed_suspects) * 2 + (1 if reveal == True else 0)
        return score

class Player():

    saveChar = None
    savePos = None
    data = None
    power = False
    saveValuePower = [None, None]

    def __init__(self):

        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()
        
    def powerLoopNb(self, charact, i):
        if (charact['color'] == "pink"):
            return 0
        if charact['color'] == "red":
            return 0

        if charact['color'] == "black":
            return 1

        if charact['color'] == "white":
            return 0
            nb = 0
            for moved_character in game.game_state['characters']:
                if moved_character['position'] == charact['position'] and charact != moved_character:
                    disp = {
                        x for x in passages[charact['position']] if x not
                        in game.game_state['blocked'] or moved_character['position'] not in game.game_state['blocked']}

                    available_positions = list(disp)
                    nb += len(available_positions)
            return nb

        if charact['color'] == "purple":
            return 7

        if charact['color'] == "brown":
            self.testBrown = []
            nb = 0
            for char in game.game_state['characters']:
                if (char == charact):
                    continue
                if (char['position'] == charact['position']):
                    self.testBrown.append(char)
                    nb += 1
            return nb

        if charact['color'] == "grey":
            return 10

        if charact['color'] == "blue":
            return 11

    def activate_power(self, charact, i, save_pos, data):
        if charact['color'] == "black":
            saveForResetPower = []
            for q in game.game_state['characters']:
                if q['position'] in {x for x in passages[charact['position']] if x not in game.game_state['blocked'] or q['position'] not in game.game_state['blocked']}:
                    saveForResetPower.append([q, q['position']])
                    game.change_character_position(q, charact['position'])
            return [saveForResetPower, [None, None]]

        if charact['color'] == "white":
            positions = []
            saveForResetPower = []
            for moved_character in game.game_state['characters']:
                if moved_character['position'] == save_pos and charact != moved_character:
                    disp = {
                        x for x in passages[charact['position']] if x not
                        in game.game_state['blocked'] or moved_character['position'] not in game.game_state['blocked']}

                    available_positions = list(disp)
                    position = available_positions[random.randint(0, len(available_positions)-1)]
                    saveForResetPower.append([moved_character, moved_character['position']])
                    moved_character['position'] = position
                    positions.append(position)
            return [saveForResetPower, [positions, None]]

        if charact['color'] == "grey":

            available_rooms = [room for room in range(10)]
            saveForResetPower = game.game_state['shadow']
            game.game_state['shadow'] = available_rooms[i]
            return [saveForResetPower, [i, None]]

        if charact['color'] == "blue":
            saveForResetPower = game.game_state['blocked'].copy()
            nb = 0
            available_rooms = [room for room in range(10)]
            for r in range(0, 10):
                selected_room = available_rooms[r]

                for selected_exit in passages[r]:
                    if (selected_exit < selected_room):
                        continue
                    if (nb == i):
                        game.game_state['blocked'] = [selected_room, selected_exit]
                        return[saveForResetPower, [selected_room, selected_exit]]
                    nb += 1
        if charact['color'] == "brown":
            nb = 0
            for char in game.game_state['characters']:
                if (char == charact):
                    continue
                if (char['position'] == save_pos):
                    if (nb == i):
                        saveForResetPower = [char, char['position']]
                        game.change_character_position(char, save_pos)
                        return [saveForResetPower, [char, None]]
                    nb += 1
        if charact['color'] == "purple":
            nb = 0
            for char in game.game_state['characters']:
                if (i == nb):
                    saveForResetPower = [char, char['position']]
                    game.change_character_position(charact, char['position'])
                    game.change_character_position(char, save_pos)
                    return [saveForResetPower, [char, None]]
                nb += 1

        return [None, [None, None]]

    def resetAfterPower(self, charact, saveForResetPower):
        if charact['color'] == "black" or charact['color'] == "white":
            for char in saveForResetPower:
                game.change_character_position(char[0], char[1])

        elif charact['color'] == "grey":
            game.game_state['shadow'] = saveForResetPower

        elif charact['color'] == "blue":
            game.game_state['blocked'] = saveForResetPower

        elif charact['color'] == "brown" or charact['color'] == "purple":
            charact['power'] = True
            game.change_character_position(saveForResetPower[0], saveForResetPower[1])
        saveForResetPower = None

    def getDestinations(self, charact):
        pass_act = pink_passages if charact['color'] == 'pink' else passages
        disp = {x for x in pass_act[charact['position']]
                if charact['position'] not in game.game_state['blocked'] or x not in game.game_state['blocked']}
        return list(disp)

    def alphabeta(self, data, depth, alpha, beta, maxDepth):
        if (depth == 0):
            return game.heuristic()
        if (((maxDepth == 4 or maxDepth == 1) and (depth == 4 or depth == 1)) or ((maxDepth == 3 or maxDepth == 2) and (depth == 3 or depth == 2))):
            value = -1000000000
            for c in data:
                charact = next(x for x in game.game_state['characters'] if x['color'] == c['color'])
                testIdx = -1
                save_pos = charact['position']
                for position in self.getDestinations(charact):
                    testIdx += 1
                    for powerUseNb in range(0, self.powerLoopNb(charact, testIdx) + 1):
                        game.change_character_position(charact, position)
                        if (powerUseNb > 0):
                            [saveForResetPower, savePow] = self.activate_power(charact, powerUseNb - 1, save_pos, data)

                        sentData = data.copy()
                        sentData.remove(c)
                        nb = self.alphabeta(sentData, depth - 1, alpha, beta, maxDepth)
                        if (value < nb):
                            value = nb
                        if (powerUseNb > 0):
                            self.resetAfterPower(charact, saveForResetPower)
                        game.change_character_position(charact, save_pos)
                        if (alpha < value):
                            alpha = value
                            if (depth == maxDepth):
                                self.saveChar = charact
                                self.savePos = position
                                if (powerUseNb > 0):
                                    self.power = True
                                    self.saveValuePower = savePow
                                else:
                                    self.power = False
                                print("saving pos " + str(position) + "for char " + charact['color'] + "\n")
                                print("value " + str(value) + "\n")
                        if (beta <= alpha):
                            return (value)
            return value
        else:
            value = 1000000000
            for c in data:
                charact = next(x for x in game.game_state['characters'] if x['color'] == c['color'])
                testIdx = -1
                save_pos = charact['position']
                for position in self.getDestinations(charact):
                    testIdx += 1
                    for powerUseNb in range(0, self.powerLoopNb(charact, testIdx) + 1):
                        game.change_character_position(charact, position)
                        if (powerUseNb > 0):
                            [saveForResetPower, savePow] = self.activate_power(charact, powerUseNb - 1, save_pos, data)

                        sentData = data.copy()
                        sentData.remove(c)
                        nb = self.alphabeta(sentData, depth - 1, alpha, beta, maxDepth)
                        if (value > nb):
                            value = nb
                        if (powerUseNb > 0):
                            self.resetAfterPower(charact, saveForResetPower)
                        game.change_character_position(charact, save_pos)
                        if (beta > value):
                            beta = value
                        if (beta <= alpha):
                            return (value)
            return value


    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        game.set_game_state(question['game state'])
        print("data " + str(data))
        print("\n")
        print(question['question type'])
        if (question['question type'] == "select character"):
            self.alphabeta(data, len(data), -1000000000, 1000000000, len(data))
            response_index = data.index(self.saveChar)
        elif (question['question type'] == "select position"):
            if (self.savePos in data):
                response_index = data.index(self.savePos)
            else:
                response_index = random.randint(0, len(data)-1)
        elif (question['question type'] == "activate " + self.saveChar['color'] + " power"):
            print("activating power of color : " + str(self.saveChar['color']))
            if (self.saveChar['color'] == "red"):
                response_index = 1
            else:
                response_index = 1 if self.power == True else 0
        else:
            print("saved values power : " + str(self.saveValuePower) + " --- data : " + str(data) + "\n\n")

            if (self.saveChar['color'] == "white" and self.saveValuePower[0] != None):
                response_index = random.randint(0, len(data)-1)
#                if (len(self.saveValuePower[0]) == 0):
#                    self.saveValuePower[0] = None
#                    response_index = random.randint(0, len(data)-1)
#                else:
#                    pos = self.saveValuePower[0].pop(0)
#                    if (pos in data):
#                        response_index = data.index(pos)
#                    else:
#                        response_index = random.randint(0, len(data)-1)
            elif (self.saveValuePower[0] != None and self.saveValuePower[0] in data):
                response_index = data.index(self.saveValuePower[0])
                self.saveValuePower[0] = None
            elif (self.saveValuePower[1] != None and self.saveValuePower[1] in data):
                response_index = data.index(self.saveValuePower[1])
                self.saveValuePower[1] = None
            else:
                response_index = random.randint(0, len(data)-1)

        print("response " + str(response_index) + "\n")
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        response = self.answer(data)
        # send back to server
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):

        self.connect()

        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True



p = Player()

game = Game()

p.run()