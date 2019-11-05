import socket
import os
import logging
from logging.handlers import RotatingFileHandler
import json
import protocol
from random import randrange
import random

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
set up inspector logging
"""
inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/inspector.log"):
    os.remove("./logs/inspector.log")
file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Character:
    """
        Class representing the eight possible characters of the game.
    """

    def __init__(self, color):
        self.color, self.suspect, self.position, self.power = color, True, 0, True

    def __repr__(self):
        if self.suspect:
            susp = "-suspect"
        else:
            susp = "-clean"
        return self.color + "-" + str(self.position) + susp

    def display(self):
        return {
            "color": self.color,
            "suspect": self.suspect,
            "position": self.position,
            "power": self.power
        }

class Game:
    
    def lumiere(self):
        partition = [{p for p in self.characters if p.position == i}
                     for i in range(10)]
        if len(partition[self.fantom.position]) == 1 or self.fantom.position == self.shadow:
            self.position_carlotta += 1
            for piece, gens in enumerate(partition):
                if len(gens) > 1 and piece != self.shadow:
                    for p in gens:
                        p.suspect = False
        else:
            for piece, gens in enumerate(partition):
                if len(gens) == 1 or piece == self.shadow:
                    for p in gens:
                        p.suspect = False
        self.position_carlotta += len(
            [p for p in self.characters if p.suspect])

    def tour(self):

        # work
        self.actions()
        self.lumiere()
        for p in self.characters:
            p.power = True
        self.num_tour += 1

    def lancer(self):
        """
            Run a game until either the fantom is discovered,
            or the singer leaves the opera.
        """
        # work
        while self.position_carlotta < self.exit and len([p for p in self.characters if p.suspect]) > 1:
            self.tour()
        # game ends
        return self.exit - self.position_carlotta

    def __repr__(self):
        message = f"Tour: {self.num_tour},\n"
        message += f"Position Carlotta / exit: {self.position_carlotta}/{self.exit},\n"
        message += f"Shadow: {self.shadow},\n"
        message += f"blocked: {self.blocked}"
        message += "".join(["\n"+str(p) for p in self.characters])
        return message

    def update_game_state(self, player_role):
        """
            representation of the global state of the game.
        """
        self.characters_display = [character.display() for character in
                                   self.characters]
        self.tiles_display = [tile.display() for tile in
                              self.tiles]
        self.active_tiles_display = [tile.display() for tile in
                                     self.active_tiles]
        # update

        self.game_state = {
            "position_carlotta": self.position_carlotta,
            "exit": self.exit,
            "num_tour": self.num_tour,
            "shadow": self.shadow,
            "blocked": self.blocked_list,
            "characters": self.characters_display,
            "active tiles": self.active_tiles_display,
        }
        
        return self.game_state

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

        return self.game_state

    def change_character_position(self, character, position):
        next(x for x in self.game_state['characters'] if x['color'] == character['color'])['position'] = position

    def heuristic(self):
        x = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for char in self.game_state['characters']:
            x[char['position']] += 1


        nb = 1
        revealed = 0
        for char in self.game_state['characters']:
            if (char['suspect'] == False):
                continue
            nb += 1
            fantom = next(x for x in self.game_state['characters'] if x['color'] == char['color'])
            reveal = True
            if (x[fantom['position']] > 1 and fantom['position'] != self.game_state['shadow']):
                reveal = False

            number_revealed_suspects = 0
            for char in self.game_state['characters']:
                if (char == fantom or char['suspect'] == False):
                    continue
                if (x[char['position']] > 1 and char['position'] != self.game_state['shadow'] and reveal == True):
                    number_revealed_suspects += 1
                if ((x[char['position']] == 1 or char['position'] == self.game_state['shadow']) and reveal == False):
                    number_revealed_suspects += 1
            revealed += number_revealed_suspects
        revealed = revealed / nb * 100
        return number_revealed_suspects

class Player():

    score = 0
    saveChar = None
    savePos = None
    data = None

    def __init__(self):

        self.end = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def alphabeta(self, data, depth, player, alpha, beta, maxDepth):
        if (depth == 0):
            return self.score
        if (player):
            value = -1000000000
            for charact in data:
                if (charact not in game.game_state['characters']):
                    continue
                save_pos = charact['position']
                pass_act = pink_passages if charact['color'] == 'pink' else passages
                if charact['color'] != 'purple' or charact['power']:
                    disp = {x for x in pass_act[charact['position']]
                            if charact['position'] not in game.game_state['blocked'] or x not in game.game_state['blocked']}
                    for position in list(disp):
                        game.change_character_position(charact, position)
                        local = self.score
                        self.score = game.heuristic()
                        if (depth == maxDepth):
                            beta = 1000000000

                        nb = self.alphabeta(data, depth - 1, player, alpha, beta, maxDepth)
                        if (value < nb):
                            value = nb
                        game.change_character_position(charact, save_pos)
                        self.score = local
                        if (alpha < value):
                            alpha = value
                            if (depth == maxDepth):
                                self.saveChar = charact
                                self.savePos = position
                                print("saving pos " + str(position) + "for char " + charact['color'] + "\n")
                                print("value " + str(value) + "\n")
                        if (beta <= alpha and depth != maxDepth):
                            return (value)
            return value
        else:
            value = 1000000000
            i = 0
            for charact in data:
                save_pos = charact['position']
                pass_act = pink_passages if charact['color'] == 'pink' else passages
                if charact['color'] != 'purple' or charact['power']:
                    disp = {x for x in pass_act[charact['position']]
                            if charact['position'] not in game.game_state['blocked'] or x not in game.game_state['blocked']}
                    for position in list(disp):
                        game.change_character_position(charact, position)
                        local = self.score
                        self.score = game.heuristic()

                        nb = self.alphabeta(data, depth - 1, player, alpha, beta, maxDepth)
                        if (value > nb):
                            value = nb
                        game.change_character_position(charact, save_pos)
                        self.score = local
                        if (beta > value):
                            beta = value
                        if (beta <= alpha):
                            return (value)
                i = i + 1
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
            self.alphabeta(data, len(data), True, -1000000000, 1000000000, len(data))
            response_index = data.index(self.saveChar)
        elif (question['question type'] == "select position"):
            if (self.savePos in data):
                response_index = data.index(self.savePos)
            else:
                response_index = random.randint(0, len(data)-1)
        elif (question['question type'] == "activate " + self.saveChar['color'] + " power"):
            if (self.saveChar['color'] == "red"):
                response_index = 1
            else:
                response_index = random.randint(0, 1)
        else:
            print("i don't know this question")
            response_index = random.randint(0, len(data)-1)


        print("response " + str(response_index) + "\n")
        # log
        inspector_logger.debug("|\n|")
        inspector_logger.debug("fantom answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {data[response_index]}")
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

    def play(self, game):

        charact = self.select(game.active_tiles,
                                game.update_game_state(1))

        moved_characters = self.activate_power(charact,
                                                game,
                                                before | two,
                                                game.update_game_state(1))

        self.move(charact,
                    moved_characters,
                    game.blocked,
                    game.update_game_state(1))

        self.activate_power(charact,
                            game,
                            after | two,
                            game.update_game_state(1))

    def select(self, t, game_state):
        """
            Choose the character to activate whithin
            the given choices.
        """
        available_characters = [character.display() for character in t]
        question = {"question type": "select character",
                    "data": available_characters,
                    "game state": game_state}
        selected_character = ask_question_json(self, question)

        # test
        # range(len(t)) goes until len(t)-1
        if selected_character not in range(len(t)):
            warning_message = (
                ' !  : selected character not in '
                'available characters. Choosing random character.'
            )
            selected_character = random.randint(0, len(t)-1)

        perso = t[selected_character]


        del t[selected_character]
        return perso

    def activate_power(self, charact, game, activables, game_state):
        """
            Use the special power of the character.
        """
        # check if the power should be used before of after moving
        # this depends on the "activables" variable, which is a set.
        if charact.power and charact.color in activables:
            character_color = charact.display()["color"]
            question = {"question type": f"activate {character_color} power",
                        "data": [0, 1],
                        "game state": game_state}
            power_activation = ask_question_json(self, question)

            if power_activation == 1:
                power_answer = "yes"
            else:
                power_answer = "no"

            # work
            if power_activation:
                charact.power = False

                # red character
                if charact.color == "red":
                    draw = game.cards[0]
                    if draw == "fantom":
                        game.position_carlotta += -1 if self.numero == 0 else 1
                    elif self.numero == 0:
                        draw.suspect = False
                    del game.cards[0]

                # black character
                if charact.color == "black":
                    for q in game.characters:
                        if q.position in {x for x in passages[charact.position] if x not in game.blocked or q.position not in game.blocked}:
                            q.position = charact.position

                # white character
                if charact.color == "white":
                    for moved_character in game.characters:
                        if moved_character.position == charact.position and charact != moved_character:
                            disp = {
                                x for x in passages[charact.position] if x not
                                in game.blocked or moved_character.position not in game.blocked}

                            # edit
                            available_positions = list(disp)
                            # format the name of the moved character to string
                            character_to_move = str(
                                moved_character).split("-")[0]
                            question = {"question type": "white character power move "+character_to_move,
                                        "data": available_positions,
                                        "game state": game_state}
                            selected_index = ask_question_json(self, question)

                            # test
                            if selected_index not in range(len(disp)):
                                warning_message = (
                                    ' !  : selected position not available '
                                    'Choosing random position.'
                                )
                                selected_position = disp.pop()

                            else:
                                selected_position = available_positions[selected_index]

                            moved_character.position = selected_position

                # purple character
                if charact.color == "purple":

                    available_characters = list(colors)
                    available_characters.remove("purple")
                    question = {"question type": "purple character power",
                                "data": available_characters,
                                "game state": game_state}
                    selected_index = ask_question_json(self, question)

                    # test
                    if selected_index not in range(len(colors)):
                        warning_message = (
                            ' !  : selected character not available '
                            'Choosing random character.'
                        )
                        selected_character = colors.pop()

                    else:
                        selected_character = available_characters[selected_index]


                    # y a pas plus simple ?
                    selected_crctr = [x for x in game.characters if x.color
                                      == selected_character][0]
                    charact.position, selected_crctr.position = selected_crctr.position, charact.position


                # brown character
                if charact.color == "brown":
                    # the brown character can take other characters with him
                    # when moving.
                    return [q for q in game.characters if charact.position == q.position]

                # grey character
                if charact.color == "grey":

                    available_rooms = [room for room in range(10)]
                    question = {"question type": "grey character power",
                                "data": available_rooms,
                                "game state": game_state}
                    selected_index = ask_question_json(self, question)

                    # test
                    if selected_index not in range(len(available_rooms)):
                        warning_message = (
                            ' !  : selected room not available '
                            'Choosing random room.'
                        )
                        selected_index = random.randint(
                            0, len(available_rooms)-1)
                        selected_room = available_rooms[selected_index]

                    else:
                        selected_room = available_rooms[selected_index]

                    game.shadow = selected_room

            # blue character
                if charact.color == "blue":

                    # choose room
                    available_rooms = [room for room in range(10)]
                    question = {"question type": "blue character power room",
                                "data": available_rooms,
                                "game state": game_state}
                    selected_index = ask_question_json(self, question)

                    # test
                    if selected_index not in range(len(available_rooms)):
                        warning_message = (
                            ' !  : selected room not available '
                            'Choosing random room.'
                        )
                        selected_index = random.randint(
                            0, len(available_rooms)-1)
                        selected_room = available_rooms[selected_index]

                    else:
                        selected_room = available_rooms[selected_index]

                    # choose exit
                    passages_work = passages[selected_room].copy()
                    available_exits = list(passages_work)
                    question = {"question type": "blue character power exit",
                                "data": available_exits,
                                "game state": game_state}
                    selected_index = ask_question_json(self, question)

                    # test
                    if selected_index not in range(len(available_exits)):
                        warning_message = (
                            ' !  : selected exit not available '
                            'Choosing random exit.'
                        )
                        selected_exit = passages_work.pop()

                    else:
                        selected_exit = available_exits[selected_index]

                    game.blocked = {selected_room, selected_exit}
                    game.blocked_list = list(game.blocked)
        return [charact]

    def move(self, charact, moved_characters, blocked, game_state):
        """
            Select a new position for the character.
        """
        pass_act = pink_passages if charact.color == 'pink' else passages
        if charact.color != 'purple' or charact.power:
            disp = {x for x in pass_act[charact.position]
                    if charact.position not in blocked or x not in blocked}

            available_positions = list(disp)
            question = {"question type": "select position",
                        "data": available_positions,
                        "game state": game_state}
            selected_index = ask_question_json(self, question)

            # test
            if selected_index not in range(len(disp)):
                warning_message = (
                    ' !  : selected position not available '
                    'Choosing random position.'
                )
                selected_position = disp.pop()

            else:
                selected_position = available_positions[selected_index]

            for q in moved_characters:
                q.position = selected_position



p = Player()

game = Game()

p.run()
