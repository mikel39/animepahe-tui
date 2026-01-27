import asyncio
import sys

from .cli import console, main


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print('\nbye bye piece of shit')
    except Exception as err:
        console.log(err)
    finally:
        sys.exit()


if __name__ == '__main__':
    start()
