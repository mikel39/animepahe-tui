from typing import Literal

import readchar
from readchar import key
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.table import Table

from .theme import Mocha


class RichMenu:
    marked = '>'
    unmarked = ' '

    def __init__(self, options: dict, title='Select an option') -> None:
        self.config = options.get('config')
        self.columns = options.get('columns', [])
        self.options = self.__sanitize(options['rows'])
        self.title = title

    def __sanitize(self, rows):
        result = list()

        for i, row in enumerate(rows):
            new_row = []

            if i == 0:
                new_row.append(self.marked)
            else:
                new_row.append(self.unmarked)

            if type(row) is tuple:
                new_row.extend([*row])
            else:
                new_row.append(row)

            result.append(new_row)

        return result

    def __generate_table(self) -> Panel:
        table = Table(
            box=None,
            padding=(0, 1),
            collapse_padding=True,
            show_header=True if self.columns else False,
            show_footer=True,
            caption='\t'.join([f'{k}:{ins}' for k, ins in self.config])
            if self.config
            else None,
            caption_justify='full',
        )

        if self.columns:
            table.add_column(' ')

        for column in self.columns:
            table.add_column(column)

        for mark, *option in self.options:
            style = Style()
            if mark == self.marked:
                style = Style(bold=True, color=Mocha.rosewater)

            table.add_row(mark, *[str(opt) for opt in option], style=style)

        return Panel(
            table,
            title=self.title,
            title_align='left',
            padding=(1, 0, 0, 0),
            border_style=Style(italic=True, color=Mocha.teal),
        )

    def __find_marked(self):
        index = 0

        for i, (mark, *_) in enumerate(self.options):
            if mark == self.marked:
                index = i
                break

        return index

    def __edit_options(self, direction: Literal['up', 'down']):
        step = 1 if direction == 'down' else -1
        index = self.__find_marked()

        self.options[index][0] = self.unmarked
        step = step + index

        if direction == 'down' and index == (len(self.options) - 1):
            step = 0

        self.options[step][0] = self.marked

    def __parse_key(self, pressed_key: str):
        if not self.config:
            return

        for keyc, inst in self.config:
            if keyc == pressed_key:
                return inst

    def run(self):
        with Live(self.__generate_table(), auto_refresh=False) as live:
            while True:
                key_pressed = readchar.readkey()

                match key_pressed:
                    case 'k' | key.UP:
                        self.__edit_options('up')
                    case 'j' | key.DOWN:
                        self.__edit_options('down')
                    case key.ENTER:
                        return self.__find_marked()
                    case letter:
                        res = self.__parse_key(letter)
                        if res:
                            return res

                live.update(self.__generate_table())
                live.refresh()
