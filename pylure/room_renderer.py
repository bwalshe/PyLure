import sys
import pygame
from pathlib import Path

from pylure.room import *
from pylure.resource import LureGameResourceManager


def main():
    window_size = (1280, 720)
    pygame.init()
    screen = pygame.display.set_mode(window_size)
    with LureGameResourceManager(Path("data")) as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        rooms = list(read_room_resources(room_bytes))
        layer_id = rooms[0].layers[0]
        pallet_id = room_palette_id(layer_id)
        decoder = PixelDecoder()
        layer_pixels = decoder.decode_layer_pixels(manager[layer_id])
        pallet = read_palette(manager[pallet_id])
        img = pygame.image.frombuffer(bytearray(layer_pixels), (SCREEN_WIDTH, len(layer_pixels) // SCREEN_WIDTH), "P")
        img.set_palette(pallet)
        img = pygame.transform.scale(img, window_size)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            screen.blit(img, img.get_rect())
            pygame.display.flip()


if __name__ == "__main__":
    main()
