# VimChanneler
Interact with Vim channels via Python scripting

# What is it

VimChanneler simple way to run and interact with a vim session from within a python script.
It provides the capability to test vim commands and vimscript functionality via python testing capabilities.  Such as the python assert statement or the python unittest module.
This uses integrates the Vim [channel](https://vimhelp.org/channel.txt.html) feature with the Python [asyncio](https://docs.python.org/3/library/asyncio.html) module capabilities.

# Quick Start

Here is an example which does the following.
1. Starts vim as a subprocess and automatically establishes a channel between vim and a python asyncio server.
1. Issues the vim "ex" command to open a file.
1. Evaluates a vim "expr" (expression) and gets the the result in the python script.
1. Automatically quits the vim subprocess at the end of processing by issuing the vim "quitall!" command.

```python
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
```

# Installation

All of the functionality is incorporated into a single python file: vim_channeler.py.  There are no dependencies on any vim plugins such as .vim files.  All that is required is a version of vim that supports channels (vim version approximately >= 7.4) and python3 that supports later asyncio (python version approximately >= 3.8).

Download either the single file vim_channeler.py or clone the repository. The in python can simply ```import vim_channeler```.

# VimChanneler capabilities

Vim commands from python can either be one-way (from python to vim) or two-way (from python to vim and then python waits for a response from vim).

| Command              | Description                                                                          |
| ---                  | ---                                                                                  |
| ex(command)          | Run a vim "ex" command                                                               |
| ex_redir(command)    | Run a vim "ex" command and redirect the textual output back to python                |
| expr(expression)     | Evaluate a vim expression and return the result back to python                       |
| call(fcn, ...)       | Call a vim function with any number of arguments and get the result back to python   |
| get_buffer_lines()   | Retrieve the text of the current vim buffer as a list of lines in python             |
| quit()               | Send a "quitall!" command to vim to completely end the session                       |

# Using the standard command line arguments

# Further examples