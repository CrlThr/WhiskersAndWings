import json

import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, 1), (0, -1)])): 1,
    tuple(sorted([(-1, 0), (0, -1)])): 5,
    tuple(sorted([(1, 0), (0, -1), (-1, 0)])): 4,
    tuple(sorted([(1, 0), (0, -1)])): 3,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 1,
    tuple(sorted([(1, 0), (-1, 0), (0, -1), (0, 1)])): 4,
}

AUTOTILE_MAP_BORDER = {
    tuple(sorted([(1, 0), (0, 1), (0, -1)])): 0,
    tuple(sorted([(1, 0), (0, 1)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1), (0, -1)])): 2,
    tuple(sorted([(-1, 0), (0, 1)])): 7,
    tuple(sorted([(-1, 0), (0, -1)])): 8,
    tuple(sorted([(1, 0), (-1, 0), (0, -1)])): 3,
    tuple(sorted([(1, 0), (-1, 0), (0, -1), (0, 1)])): 4,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, 1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'egypt_wood', 'brick', 'stone_border', 'egypt_border', 'barrier', 'egypt_platform'}
DEATH_TILES = {'traps'}
CHEST_TILES = {'chest'}
KEY_TILES = {'key'}
LEVER_TILES = {'lever'}
BUTTON_TILES = {'button'}
DOOR_TILES = {'door'}
BARRIER_TILES = {'barrier'}
MOVING_TILES = {'egypt_platform'}
DEST_TILES = {'platform_dest'}
AUTOTILE_TYPES = {'egypt_wood'}
RAT_TILES = {'Rat'}
AUTOTILE_BORDERS = {'stone_border', 'egypt_border'}
PLATFORM_TILES = {'platform'}



class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def check_tile(self, tiletype):
        tiles = []
        for loc in self.tilemap:
            for types in tiletype:
                if self.tilemap[loc]['type'] == types:
                    tiles.append(self.tilemap[loc])
        return tiles

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def solid_check_platform(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PLATFORM_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects
    
    def platform_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PLATFORM_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size - 43))
        return rects

    def chest_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in CHEST_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def button_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in BUTTON_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def lever_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in LEVER_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def key_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in KEY_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def door_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in DOOR_TILES:
                rects.append(
                    pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,
                                self.tile_size))
        return rects

    def death_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):  # collision with traps
            if tile['type'] in DEATH_TILES:
                if tile['variant'] == 0 or tile['variant'] == 4:  # collision traps down
                    rects.append(
                        pygame.Rect(tile['pos'][0] * self.tile_size,
                                    (tile['pos'][1] * (self.tile_size)) + self.tile_size // 1.5,
                                    self.tile_size, self.tile_size // 3))
                elif tile['variant'] == 2 or tile['variant'] == 6:  # collision traps up
                    rects.append(
                        pygame.Rect(tile['pos'][0] * self.tile_size,
                                    (tile['pos'][1] * (self.tile_size)),
                                    self.tile_size, self.tile_size // 3))
                elif tile['variant'] == 3 or tile['variant'] == 7:  # collision traps up
                    rects.append(
                        pygame.Rect(tile['pos'][0] * self.tile_size,
                                    (tile['pos'][1] * (self.tile_size)),
                                    self.tile_size // 3, self.tile_size))
                elif tile['variant'] == 1 or tile['variant'] == 5:  # collision traps up
                    rects.append(
                        pygame.Rect((tile['pos'][0] * self.tile_size) + self.tile_size // 1.5,
                                    (tile['pos'][1] * (self.tile_size)),
                                    self.tile_size // 3, self.tile_size))
        return rects

    def chest_state(self, pos):
        if self.game.chest:
            self.key_enable()
            for tile in self.tiles_around(pos):
                if tile['type'] in CHEST_TILES:
                    tile['variant'] = 1

    def button_state(self, pos):
        if self.game.button:
            for tile in self.tiles_around(pos):
                if tile['type'] in BUTTON_TILES:
                    tile['variant'] = 1
            self.barrier_remove()

    def lever_state(self, pos):
        if self.game.lever:
            for tile in self.tiles_around(pos):
                if tile['type'] in LEVER_TILES:
                    tile['variant'] = 0
            self.plat_move()

    def barrier_remove(self):
        for tile in self.check_tile(BARRIER_TILES):
            tile['pos'][0] = 64

    def plat_move(self):
        if not self.game.platform_has_moved:
            for tile in self.check_tile(MOVING_TILES):
                tile['pos'][1] = 64
            for dest in self.check_tile(DEST_TILES):
                dest['type'] = 'egypt_platform'
            self.game.platform_has_moved = True

    def key_enable(self):
        for tile in self.check_tile(KEY_TILES):
            if tile['variant'] == 0:
                tile['variant'] = 1
                self.game.key_state = 1

    def key_disable(self):
        for tile in self.check_tile(KEY_TILES):
            if tile['variant'] == 1:
                tile['variant'] = 0
                self.game.key_state = 2

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]
            elif (tile['type'] in AUTOTILE_BORDERS) and (neighbors in AUTOTILE_MAP_BORDER):
                tile['variant'] = AUTOTILE_MAP_BORDER[neighbors]

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']],
                      (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']],
                              (
                                  tile['pos'][0] * self.tile_size - offset[0],
                                  tile['pos'][1] * self.tile_size - offset[1]))
