import datetime
from random import random
import time
from rich.console import Group
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

count = 0

console = Console()
layout = Layout()

connection_status = Status("[red]Connecting to socket")
focus_status = Status("[red]Minecraft not focused")

# Setup layout
layout.split_column(Layout(name="upper"), Layout(name="lower"))

LOGS = []


table = Table(title="Photographer")
with Live(console=console, screen=True, refresh_per_second=10) as live_table:
    is_connected = True
    is_focused = True

    while True:
        is_connected = not is_connected if random() < 0.2 else is_connected
        is_focused = not is_focused if random() < 0.2 else is_focused

        time.sleep(0.1)
        live_table.update(
            Group(
                f":white_check_mark:127.0.0.1:1233" if is_connected else connection_status,
                f":white_check_mark:Focused" if is_focused else focus_status,
            )
        )

    # while True:
    #     time.sleep(0.5)
    # live_table.update(Status("Minecraft focused", spinner="earth"))
    # live_table.update(Panel("test", expand=False))


console.print(Panel("test \nnew line maybe?? I hope"))

exit()

table = Table()
table.add_column("ID")
table.add_column("Time")
table.add_column("Success")

with Live(table, refresh_per_second=4):  # update 4 times a second to feel fluid
    for row in range(12):
        time.sleep(0.4)  # arbitrary delay
        # update the renderable internally
        table.add_row(f"{row}", f"{datetime.datetime.now()}", "[red]ERROR")

# with Live() as live:
#     while True:
#         live.console.print(f"Count: {count}")
#         live.console.up
#         count += 1
#         time.sleep(1)
