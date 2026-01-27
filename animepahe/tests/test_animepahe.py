from pprint import pprint
from typing import TypedDict

import pytest
from pydantic import TypeAdapter
from typing_extensions import Type

from ..anime_pahe import AnimePahe
from ..types import EpisodeByAnime, EpisodeOptions, SearchResult

ani = AnimePahe()

anime_session = '66ce33ff-272c-6c23-6403-6ac1ad135acb'
episode_session = 'fa3c39568bf556a7c8b660b7064462a6a2f49f86d48093ec7df245c0dd00b14a'


@pytest.mark.asyncio(loop_scope='session')
async def test_init():
    init = await ani.initialize()
    assert init is True


@pytest.mark.asyncio(loop_scope='session')
async def test_get_episodes_options():
    res = await ani.get_episode_options(anime_session, episode_session)
    TypeAdapter(EpisodeOptions).validate_python(res)


@pytest.mark.asyncio(loop_scope='session')
async def test_get_episodes_by_anime():
    res = await ani.get_episodes_by_anime(anime_session)

    for episode in res:
        TypeAdapter(EpisodeByAnime).validate_python(episode)


@pytest.mark.asyncio(loop_scope='session')
async def test_search():
    query = 'tokyo'
    res = await ani.search(query)

    for anime in res:
        TypeAdapter(SearchResult).validate_python(anime)
