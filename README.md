# VimChanneler

Interact with the Vim editor channels via Python scripting.

# What is it

VimChanneler is a simple way to run and interact with a vim session from within a python script.
It allows for the remote control of vim via python function calls.
As such it provides the capability to test vim commands and vimscript functionality via python testing capabilities.  Such as the python assert statement or the python unittest module.
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

All of the functionality is incorporated into a single python file: [vim_channeler.py].  There are no dependencies on any vim plugins such as .vim files.  All that is required is a version of vim that supports channels (vim version approximately >= 7.4) and python3 that supports later asyncio (python version approximately >= 3.8).

Download either the single file [vim_channeler.py] or clone the repository. Then in python can simply ```import vim_channeler```.

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

The example in the [Quick Start](#quick-start) section is in the file [vim_channeler_simplest_test.py](vim_channeler_simplest_test.py).  It can be run from the command line like:
```sh
$ ./vim_channeler_simplest_test.py
```

A slightly longer example is provided in [vim_channeler_example.py](vim_channeler_example.py).  This example runs multiple scenarios, including the use of the python **assert** call.  In addition, it utilizes the **vim_channeler_argparser()** which is part of [vim_channeler.py](vim_channeler.py).  This is a wrapper around the python [argparse.ArgumentParser](https://docs.python.org/3/library/argparse.html#argumentparser-objects) to support a standard set of command line arguments to python scripts utilizing a **VimChanneler**.

```sh
$ ./vim_channeler_example.py
```

By default this will run the console **vim** executable as a subprocess and then quit the vim process and the end resulting in the subprocess ending cleanly.

However the gui version of vim such as **gvim** or **mvim** (MacOS) can used instead by supplying the **-g** or **--use-gui-vim** command line parameter to the script.  This will start the gui version of vim and leave it running so is easy to see the result of the VimChanneler python scenarios by visually inspecting the gvim window.  In other words it will not **quit** the vim subprocess.
```sh
$ ./vim_channeler_example.py -g
```

To use the gui version of vim and then automatically quit at the end use the **-q** or **--quit-vim** command line parameter:
```sh
$ ./vim_channeler_example.py -g -q
```

By default VimChanneler will start vim in [clean mode](https://vimhelp.org/starting.txt.html#--clean) in order to focus exclusively on the python interaction.  However to start vim with normal startup where all user customizations are include use **-i** or **--initialize-vim**.
```sh
$ ./vim_channeler_example.py -i
```

Help is supported:
```
$ ./vim_channeler_example.py -h
usage: vim_channeler_example.py [-h] [-g] [-i] [-q] [-e VIM_EXECUTABLE] [-l VIM_CHANNEL_LOG] [--host HOST] [--port PORT] [-v]

Run vim channeler simple tests

options:
  -h, --help            show this help message and exit
  -g, --use-gui-vim     Test gui version of vim such as gvim or mvim
  -i, --initialize-vim  Start vim with default initialization (not --clean)
  -q, --quit-vim        Quit vim when scenario finished
  -e VIM_EXECUTABLE, --vim-executable VIM_EXECUTABLE
                        Vim executable to use instead of vim, gvim or mvim
  -l VIM_CHANNEL_LOG, --vim-channel-log VIM_CHANNEL_LOG
                        Vim ch_logfile to use, example: -l=/tmp/vimch.log
  --host HOST           Host to use for vim channel
  --port PORT           Port to use for vim channel
  -v, --verbose         verbose debug logging
```

See the python function ```vim_channeler_argparser()``` in [vim_channeler.py](vim_channeler.py) for reference.

# Python unittest module

A python test fixture can be created by inheriting from VimChannelerFixture which itself is derived from the python [unittest.IsolatedAsyncioTestCase](https://docs.python.org/3/library/unittest.html#unittest.IsolatedAsyncioTestCase).  See [vim_channeler_unittest.py](vim_channeler_unittest.py) an example containing the following.

```python
class VimChannelerSimpleTest(VimChannelerFixture):

    async def test_edit_file1(self):
        vimch = await self.createVimChanneler()   # create a VimChanneler for use by this test
        await vimch.ex('edit /tmp/a.tmp')         # open a file in the vim session
        f1 = await vimch.ex_redir('f')            # execute the vim command 'f' (file) which reports the current open file
        print('f1={}'.format(f1))                 # print the result on the console
        self.assertTrue('a.tmp' in f1)            # assert via the python unittest module capabilities
        await vimch.ex('redraw')                  # redraw vim (relevant only for gui mode such as gvim, mvim)
```

Each test case with in the test suite defined within a subclass of VimChannelerFixture is run against a separate session of vim.

When running from the command line both the VimChanneler and unittest arguments can be specified:
```
$ ./vim_channeler_unittest.py -k test_edit_file1 --use-gui-vim
```

In the example above the **-k** option is specific to the unittest module and indicates that a specific test in the test suite should be run.  The **--use-gui-vim** option is recognized by the VimChanneler and indicates that the gui version of vim should be used for the test.
