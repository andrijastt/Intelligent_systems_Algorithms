import math
import pprint
import random
import sys

import pygame
import os
import config

from itertools import permutations
import copy


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]


class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [0]
        current = 0
        for i in range(1, len(coin_distance)):
            min_num = 0
            cnt = 0
            while min_num == 0 and cnt < len(coin_distance):
                if cnt not in path:
                    min_num = coin_distance[current][cnt]
                    min_index = cnt
                cnt += 1

            for j in range(0, len(coin_distance[current])):
                if j != current and coin_distance[current][j] < min_num and j not in path:
                    min_num = coin_distance[current][j]
                    min_index = j

            path.append(min_index)
            current = min_index

        return path + [0]


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):

        path = [i for i in range(1, len(coin_distance))]
        perms = list(permutations(path))

        all_paths = []
        all_lengths = []
        for perm in perms:
            temp = list(perm)
            path = [0] + temp + [0]

            length = 0
            for node in range(0, len(path) - 1):
                length += coin_distance[path[node]][path[node + 1]]

            all_lengths.append(length)
            all_paths.append(path)

        min_index = all_lengths.index(min(all_lengths))
        min_path = all_paths[min_index]

        return min_path


class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):

        all_paths = []
        for i in range(1, len(coin_distance)):
            path = {"path": [0, i], "length": coin_distance[0][i]}
            all_paths.append(path)

        good_path = []
        while True:
            path = min(all_paths, key=lambda x: x['length'])
            path_last = path["path"][len(path["path"]) - 1]
            for i in range(1, len(coin_distance)):
                new_path = copy.deepcopy(path)
                if i not in new_path["path"]:
                    new_path["length"] += coin_distance[path_last][i]
                    new_path["path"].append(i)
                    all_paths.append(new_path)

                if len(new_path["path"]) == len(coin_distance):
                    good_path = new_path["path"]

            all_paths.remove(path)
            if len(good_path) == len(coin_distance):
                break

        good_path.append(0)
        return good_path


class Micko(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def generate_MST(self, coin_distance, includes):
        distance = 0

        edges_checked = []
        edges_connected = 0
        edges_needed = len(includes) - 1

        if edges_needed == 0:
            return distance

        matrix_reachable = []
        for i in range(0, len(coin_distance)):
            row = []
            for j in range(0, len(coin_distance)):
                    if i != j or i not in includes or j not in includes:
                        row.append(False)
                    else:
                        row.append(True)
            matrix_reachable.append(row)

        while edges_connected < edges_needed:
            minimal_edge = sys.maxsize

            for i in range(0, len(coin_distance)):
                for j in range(0, len(coin_distance)):
                    if i in includes and j in includes and coin_distance[i][j] < minimal_edge and coin_distance[i][j] != 0\
                            and [i, j] not in edges_checked:
                        minimal_edge = coin_distance[i][j]
                        edge = [i, j]
                        neg_edge = [j, i]

            edges_checked.append(edge)
            edges_checked.append(neg_edge)

            if edges_connected == 0:
                edges_connected += 1
                distance += minimal_edge

                matrix_reachable[edge[0]][edge[1]] = True
                matrix_reachable[edge[1]][edge[0]] = True

            else:
                cycle = False
                for i in range(0, len(includes)):
                    if matrix_reachable[i][edge[0]] and matrix_reachable[i][edge[1]]:
                        cycle = True
                        break

                if not cycle:
                    edges_connected += 1
                    distance += minimal_edge

                    matrix_reachable[edge[0]][edge[1]] = True
                    matrix_reachable[edge[1]][edge[0]] = True

                    # azuriranje Matrice dostiznosti
                    # for i in range(0, len(includes)):
                    #     for j in range(0, len(includes)):
                    #
                    #         if matrix_reachable[i][j] and i != j:
                    #             for k in range(0, len(includes)):
                    #                 if k != i and matrix_reachable[j][k] and k != j:
                    #                     matrix_reachable[i][k] = True

                    # mozda krace resenje, smanjuje se slozenost
                    for i in range(0, len(includes)):
                        if matrix_reachable[i][edge[0]] and i != edge[0]:
                            for j in range(0, len(includes)):
                                if j != i and matrix_reachable[edge[0]][j] and edge[0] != j:
                                    matrix_reachable[i][j] = True

        return distance

    def get_agent_path(self, coin_distance):

        all_paths = []
        includes = []
        for i in range(0, len(coin_distance)):
            includes.append(i)

        distance = self.generate_MST(coin_distance, includes)

        for i in range(1, len(coin_distance)):
            path = {"path": [0, i], "length": coin_distance[0][i], "distance": distance, "combined": coin_distance[0][i] + distance}
            all_paths.append(path)

        good_path = []
        while True:
            path = min(all_paths, key=lambda x: x['combined'])
            path_last = path["path"][len(path["path"]) - 1]
            for i in range(1, len(coin_distance)):
                new_path = copy.deepcopy(path)
                if i not in new_path["path"]:
                    new_path["length"] += coin_distance[path_last][i]
                    new_path["path"].append(i)
                    temp = [x for x in includes if x not in new_path["path"]]
                    temp.append(0)
                    distance1 = self.generate_MST(coin_distance, temp)
                    new_path["distance"] = distance1
                    new_path["combined"] = new_path["length"] + distance1
                    all_paths.append(new_path)

                if len(new_path["path"]) == len(coin_distance):
                    good_path = new_path["path"]

            all_paths.remove(path)
            if len(good_path) == len(coin_distance):
                break

        good_path.append(0)
        return good_path

