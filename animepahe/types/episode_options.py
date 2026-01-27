from typing import TypedDict


class Data(TypedDict):
    audio: str
    resolution: str
    src: str


class EpisodeOptions(TypedDict):
    title: str
    data: list[Data]
