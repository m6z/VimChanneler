#!/usr/bin/env python3
from vim_channeler import VimChanneler
from pathlib import Path

async def scenario(vimch):
    # Open this file in vim as read only (view)
    path = Path(__file__).resolve()
    print(f'opening in vim: {path}')
    await vimch.ex(f'view {path}')
    # Retrieve the number of lines
    line_count = await vimch.expr("line('$')")
    print(f'line_count={line_count}')

vimch = VimChanneler()
vimch.process(scenario)
