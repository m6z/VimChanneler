#!/usr/bin/env python3

# Copyright 2022 Michael Graz
# Released under the MIT License: http://www.opensource.org/licenses/mit-license.php

import sys, json, asyncio, logging, pathlib, argparse, unittest, datetime

def vim_channeler_argparser():
    # Construct a command line argument parser for VimChanneler parameters
    # TODO add help, and examples
    parser = argparse.ArgumentParser(description='Run vim channeler simple tests')
    parser.add_argument('-g', '--use-gui-vim', action='store_true', default=False, help='Test gui version of vim such as gvim or mvim')
    # parser.add_argument('-1', '--single-instance', action='store_true', default=False, help='Only single instance of vim process')
    parser.add_argument('-i', '--initialize-vim', action='store_true', default=False, help='Start vim with default initialization (not --clean)')
    parser.add_argument('-q', '--quit-vim', action='store_true', default=False, help='Quit vim when scenario finished')
    parser.add_argument('-e', '--vim-executable', help='Vim executable to use instead of vim, gvim or mvim')
    parser.add_argument('-l', '--vim-channel-log', help='Vim ch_logfile to use, example: -l=/tmp/vimch.log')
    parser.add_argument('--host', default='localhost', help='Host to use for vim channel')
    parser.add_argument('--port', default=8765, type=int, help='Port to use for vim channel')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='verbose debug logging')
    return parser

#----------------------------------------------------------------------

class VimChanneler:

    @classmethod
    def createFromArgs(cls, vim_channeler_args):
        return cls(**vars(vim_channeler_args))

    @classmethod
    async def createAndInitializeFromArgs(cls, vim_channeler_args):
        vimch = cls(**vars(vim_channeler_args))
        await vimch.initialize()
        return vimch

    def __init__(self, use_gui_vim=False, initialize_vim=False, quit_vim=False,
            vim_executable=None, vim_channel_log=None, host='localhost', port=8765, is_console_vim=None,
            verbose=False):
        # TODO put in help

        self._logger = logging.getLogger('vim_channeler')
        self._initialize_vim = initialize_vim
        self._quit_vim = quit_vim
        self._host = host
        self._port = port
        self._vim_channel_log = vim_channel_log
        self._verbose = verbose

        if vim_executable is None:
            if use_gui_vim:
                self.vim_executable = 'mvim' if sys.platform == 'darwin' else 'gvim'
            else:
                self.vim_executable = 'vim'
        else:
            self.vim_executable = vim_executable

        if is_console_vim is None:
            # attempt to discern if this is vim or gui variant like gvim
            self.is_console_vim = pathlib.Path(self.vim_executable).stem.lower() == 'vim'
        else:
            self.is_console_vim = is_console_vim

        self._server = None
        self._reader = None
        self._writer = None
        self._connected = None
        self._subprocess = None
        self._request_number_last = 0
        self._initialized = False

        if self._verbose:
            logging.basicConfig(level=logging.DEBUG)

    def process(self, scenario):
        self._my_event_loop().run_until_complete(self._process_internal(scenario))

    def close(self):
        self._my_event_loop().run_until_complete(self.check_vim_quit())

    async def initialize(self):
        if self._initialized:
            return

        self._connected = self._my_event_loop().create_future()
        await self._create_channel()
        await self._start_vim_process()

        # A TimeoutError exception here will indicate that a vim channel never connected.
        try:
            await asyncio.wait_for(self._connected, timeout=2)
        except asyncio.exceptions.TimeoutError as e:
            msg = f"Vim channel never connected. Call ch_open('{self._host}:{self._port}') from vim"
            raise RuntimeError(msg) from e

        self._initialized = True

    async def check_vim_quit(self):
        # if running and self.quit_vim, then try to quit vim
        if self._quit_vim:
            try:
                await self.quit()
            except ConnectionResetError:
                # Not considered an error if connection already closed
                pass

    def _get_vim_args(self):
        # Build the command line args for the child vim process
        vim_args = [self.vim_executable]
        if self.is_console_vim:
            vim_args += ['--not-a-term']
            # no point in leaving headless console vim running, force quit
            self._quit_vim = True

        if not self._initialize_vim:
            vim_args += ['--clean']
        if self._vim_channel_log:
            vim_args += ['--cmd', f'call ch_logfile("{self._vim_channel_log}", "w")']
        vim_args += ['--cmd', 'set noswapfile']
        vim_args += ['--cmd', 'set noundofile']

        # first test that the port is free?
        vim_args += ['--cmd', f'let chn=ch_open("{self._host}:{self._port}")']
        return vim_args

    def _my_event_loop(self):
        loop = asyncio.get_event_loop()
        if self._verbose:
            loop.set_debug(True)
        return loop

    async def _start_vim_process(self):
        if self.is_console_vim:
            # when using console vim, stdout and stderr should be pipes
            stdout, stderr = asyncio.subprocess.PIPE, asyncio.subprocess.PIPE
        else:
            # when using gvim, stdout and stderr should be DEVNULL
            stdout, stderr = asyncio.subprocess.DEVNULL, asyncio.subprocess.DEVNULL

        vim_args = self._get_vim_args()
        self._subprocess = await asyncio.create_subprocess_exec(*vim_args,
                stdin=asyncio.subprocess.DEVNULL, stdout=stdout, stderr=stderr)

    async def _create_channel(self):
        class ServerCallback:
            def __init__(self, scope):
                self.scope = scope
            def __call__(self, reader, writer):
                self.scope._reader = reader
                self.scope._writer = writer
                self.scope._connected.set_result(True)
        # start server and wait for connection
        self._server = await asyncio.start_server(ServerCallback(self), self._host, self._port)

    async def _process_internal(self, scenario):
        await self.initialize()

        # run one or multiple scenarios in case of list or tuple
        if type(scenario) in (list, tuple,):
            for s in scenario:
                await s(self)
        else:
            await scenario(self)

        if not self.is_console_vim:
            # redraw for convenience
            await self.ex('redraw')
            # force a round trip message to get into a good state?
            # await self.expr("v:true")

    async def send(self, command):
        self._logger.debug(f'send command="{command}" server={self._server.is_serving()}')
        encoded = json.dumps(command)
        self._writer.write(encoded.encode('utf-8'))
        await self._writer.drain()

    async def send_receive(self, command, request_number=None):
        if request_number is None:
            self._request_number_last += 1
            request_number = self._request_number_last
        command.append(request_number)
        await self.send(command)
        data = await self._reader.read(8192)
        try:
            decoded = json.loads(data)
        except ValueError:
            print("ERROR json decoding failed")
            decoded = [-1, '']
        if decoded[0] != request_number:
            print('ERROR message returned out of sequence, received={} expecting={}'.format(decoded[0], request_number))
        # return decoded[1:]
        return decoded[1]

    async def ex(self, command):
        # Send a simple :ex command to vim
        await self.send(['ex', command])

    async def ex_redir(self, command):
        # Send a simple :ex command to vim, and get the command output via redirection
        vim_variable = datetime.datetime.now().strftime('var_%Y%m%d%H%M%S')
        await self.ex(f'redir => {vim_variable}')
        await self.ex(f'silent {command}')
        await self.ex('redir END')
        result = await self.expr(f'{vim_variable}')
        await self.ex(f'unlet {vim_variable}')
        return result

    async def expr(self, expression):
        return await self.send_receive(['expr', expression])

    async def call(self, vim_fcn, *vim_fcn_args):
        return await self.send_receive(['call', vim_fcn, vim_fcn_args])

    async def get_buffer_lines(self):
        # This is a way of retrieving a vim buffer line by line.
        # It is a way to retreived large buffers (greater than the reader.read() size
        text = []
        line_count = await self.expr("line('$')")
        for i in range(line_count):
            text.append(await self.expr(f'getline({i+1})'))
        return text

    async def quit(self):
        # await self.expr("v:true")  # force a roundtrip
        await self.ex('quitall!')
        await self._subprocess.communicate()

#----------------------------------------------------------------------

class VimChannelerFixture(unittest.IsolatedAsyncioTestCase):
    # Derive from this class for unit tests
    vim_channeler_args = {}
    vim_channeler_port = None

    async def createVimChanneler(self):
        # Create a new instance of a VimChanneler based on the class supplied args.
        # Increment the port number for subsequent calls.
        args = VimChannelerFixture.vim_channeler_args
        if type(args) is not type({}):
            args = vars(args).copy()
        if 'port' in args:
            if VimChannelerFixture.vim_channeler_port:
                args['port'] = VimChannelerFixture.vim_channeler_port + 1
            VimChannelerFixture.vim_channeler_port  = args['port']
        vimch = VimChanneler(**args)
        await vimch.initialize()
        self.addAsyncCleanup(self.closeVimChanneler, vimch)
        return vimch

    async def closeVimChanneler(self, vimch):
        await vimch.check_vim_quit()

#----------------------------------------------------------------------

def set_vim_channeler_event_loop_policy():
    if sys.platform != 'win32':
        return  # this is only useful for Windows Proactor implementation in asyncio

    import asyncio
    from asyncio.windows_events import ProactorEventLoop, WindowsProactorEventLoopPolicy

    class VimChanneler_ProactorEventLoop(ProactorEventLoop):

        # prevent automatic stopping of child process
        async def _make_subprocess_transport(self, *args, **kwargs):
            result = await super()._make_subprocess_transport(*args, **kwargs)
            result.close = lambda: None
            return result

        # prevent automatic closing of pipes
        def _make_socket_transport(self, *args, **kwargs):
            result = super()._make_socket_transport(*args, **kwargs)
            result.close = lambda: None
            return result

    class VimChanneler_WindowsProactorEventLoopPolicy(WindowsProactorEventLoopPolicy):
        _loop_factory = VimChanneler_ProactorEventLoop

    asyncio.set_event_loop_policy(VimChanneler_WindowsProactorEventLoopPolicy())
