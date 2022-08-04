#!/usr/bin/env python3

import asyncio, logging
from pprint import pprint
from pathlib import Path
from vim_channeler import VimChanneler, vim_channeler_argparser

def simple_test(vim_channeler_args):

    async def scenario1(vimch):
        # Open this file in vim as read only (view)
        path = Path(__file__).resolve()
        print('-- opening in vim:', path)
        await vimch.ex(f'view {path}')
        # Retrieve the number of lines
        line_count = await vimch.expr("line('$')")
        print(f'line_count={line_count}')
        assert line_count > 0

        await vimch.ex('function! Adder(x,y) \n return a:x+a:y \n endfunction')
        function = await vimch.ex_redir('function Adder')
        print(f'created function: {function}')
        result = await vimch.call('Adder', 1, 2)
        print(f'Adder(1,2)={result}')
        assert result == 3

    async def scenario2(vimch):
        scriptnames = await vimch.ex_redir('scriptnames')
        scriptnames = [x for x in scriptnames.splitlines() if x]
        print('scripts loaded:')
        pprint(scriptnames)

        text = await vimch.get_buffer_lines()
        print('first lines of file:')
        pprint(text[:5])

    vimch = VimChanneler.createFromArgs(vim_channeler_args)
    vimch.process([scenario1, scenario2])
    vimch.close()  # will quit vim if param quit_vim==True

#----------------------------------------------------------------------

def _main():
    parser = vim_channeler_argparser()
    args = parser.parse_args()
    print('== args={}'.format(args))
    simple_test(args)

if __name__ == '__main__': _main()

