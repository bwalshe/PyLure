from pathlib import Path
import click

from pylure.resource import LureFileResourceLoader, file_for_id
from pylure.room import RoomResource, read_room_resources, ROOM_DATA_RESOURCE_ID


def print_summary(room: RoomResource) -> None:
    files_used = set(file_for_id(l) for l in room.layers if l != 0)
    print(room.room_number, room.num_layers,
          list(room.layers), files_used, sep='\t')


def print_info(root: Path) -> None:
    data_path = root / file_for_id(ROOM_DATA_RESOURCE_ID)
    with data_path.open("rb") as data:
        loader = LureFileResourceLoader(data)
        room_data = loader[ROOM_DATA_RESOURCE_ID]
        print("Room\tNum\tLayer\tFile\tData Files")
        print("Number\tLayers\tId\tUsed")
        for room in read_room_resources(room_data):
            print_summary(room)


@click.command()
@click.argument("root", default="./data")
def main(root: str):
    print_info(Path(root))
