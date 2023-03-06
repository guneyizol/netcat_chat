import asyncio
import json
import sys
import signal
import aioconsole


def keyboardInterruptHandler(signal, frame):
    print('\nexiting')
    sys.exit(0)


signal.signal(signal.SIGINT, keyboardInterruptHandler)

ip_dict = {}
myip = '192.168.1.0'
myname = 'name'


async def send_hello_to_ip(ip, myip):
    if ip not in ip_dict.values():
        proc = await asyncio.create_subprocess_exec(
            'nc', ip, '12345',
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

        proc.stdin.write((json.dumps({
            'type': 'hello',
            'myname': myname,
            'myip': myip
        }
        ) + '\n').encode()
        )

        try:
            data = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
            line = data.decode().rstrip()
            if line:
                hello_message = json.loads(line)
                if hello_message.get('type') == 'aleykumselam':
                    try:
                        ip_dict[
                            hello_message['myname']
                        ] = hello_message['myip']
                    except KeyError:  # ignore invalid responses
                        pass
        except asyncio.exceptions.TimeoutError:
            pass

        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.exceptions.TimeoutError:
            proc.kill()


async def listen(myip):
    proc = await asyncio.create_subprocess_exec(
        'nc', '-lk', '12345',
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )
    while True:
        data = await proc.stdout.readline()
        line = data.decode().rstrip()
        if line:
            hello_message = json.loads(line)

            if hello_message.get('type') == 'hello':
                try:
                    ip_dict[hello_message['myname']] = hello_message['myip']
                    proc.stdin.write(
                        (json.dumps({
                            'type': 'aleykumselam',
                            'myname': myname,
                            'myip': myip
                        }
                        ) + '\n').encode()
                    )
                except KeyError:
                    pass
            elif hello_message.get('type') == 'message':
                try:
                    await aioconsole.aprint(hello_message['myip'], ':', hello_message['content'])
                except KeyError:
                    pass


async def send_hello(myip):
    while True:
        task_list = []
        for i in range(2, 256):
            ip = '192.168.1.' + str(i)

            if ip != myip:
                hello_task = asyncio.create_task(send_hello_to_ip(ip, myip))
                task_list.append(hello_task)

        await asyncio.gather(*task_list)
        await asyncio.sleep(5)


async def send_message():
    ip = await aioconsole.ainput('enter recipient IP: ')
    message = await aioconsole.ainput('enter your message (end it with a newline): ')

    proc = await asyncio.create_subprocess_exec(
        'nc', ip, '12345',
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    proc.stdin.write((json.dumps({
        'type': 'message',
        'content': message,
        'myip': myip
    }
    ) + '\n').encode()
    )
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.exceptions.TimeoutError:
        proc.kill()


async def control():
    key = await aioconsole.ainput('To send a message, press M\n'
                                  'To see the available recipient IPs, press A\n'
                                  'To exit, press E\n')
    while True:
        key = key.lower()
        if key == 'm':
            if not ip_dict:
                await aioconsole.aprint('There are no available recipients. Try later.')
            else:
                await asyncio.create_task(send_message())
        elif key == 'a':
            if not ip_dict:
                await aioconsole.aprint('There are no available recipients.')
            for name, ip in ip_dict.items():
                await aioconsole.aprint(f'{name}: {ip}')
        elif key == 'e':
            sys.exit(0)

        key = await aioconsole.ainput()


async def main():
    global myip
    myip = await aioconsole.ainput('Enter your ip: ')

    global myname
    myname = await aioconsole.ainput('Enter your name: ')

    listen_task = asyncio.create_task(listen(myip))
    hello_task = asyncio.create_task(send_hello(myip))
    control_task = asyncio.create_task(control())

    await asyncio.gather(listen_task, hello_task, control_task)


asyncio.get_event_loop().run_until_complete(main())
