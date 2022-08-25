#!/usr/bin/env python3

import sys, unittest
from vim_channeler import VimChannelerFixture, vim_channeler_argparser, set_vim_channeler_event_loop_policy

class VimChannelerSimpleTest(VimChannelerFixture):

    async def test_edit_file1(self):
        vimch = await self.createVimChanneler()   # create a VimChanneler for use by this test
        await vimch.ex('edit /tmp/a.tmp')         # open a file in the vim session
        f1 = await vimch.ex_redir('f')            # execute the vim command 'f' (file) which reports the current open file
        print('f1={}'.format(f1))                 # print the result on the console
        self.assertTrue('a.tmp' in f1)            # assert via the python unittest module capabilities
        await vimch.ex('redraw')                  # redraw vim (relevant only for gui mode such as gvim, mvim)

    async def test_edit_file2(self):
        vimch = await self.createVimChanneler()
        await vimch.ex('edit /tmp/b.tmp')
        f2 = await vimch.ex_redir('f')
        print('f2={}'.format(f2))
        self.assertTrue('b.tmp' in f2)
        await vimch.ex('redraw')

#----------------------------------------------------------------------

if __name__ == '__main__':
    parser = vim_channeler_argparser()
    # separate vim scenario args and unit test args
    vimch_args, unittest_args = parser.parse_known_args()
    print(f'vimch_args={vimch_args}')
    print(f'unittest_args={unittest_args}')

    # relevant for windows os
    set_vim_channeler_event_loop_policy()

    VimChannelerFixture.vim_channeler_args = vimch_args
    unittest.main(argv=[sys.argv[0]] + unittest_args)
