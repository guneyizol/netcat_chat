import asyncio
import json
import sys
import signal


def keyboardInterruptHandler(signal, frame):
    print('\nexiting')
    sys.exit(0)


signal.signal(signal.SIGINT, keyboardInterruptHandler)

ip_dict = {}
myip = '192.168.1.0'
myname = 'name'

async def send_hello_to_ip(ip, myip):
    proc = await asyncio.create_subprocess_exec(
        'nc', str(ip), '12345',
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    proc.stdin.write((json.dumps({
        'type': 'hello',
        'myname': 'guney',
        'myip': myip
    }
    ) + '\n').encode()
    )

    data = await proc.stdout.readline()
    line = data.decode().rstrip()
    if line:
        hello_message = json.loads(line)
        if hello_message.get('type') == 'aleykumselam':
            try:
                ip_dict[
                    hello_message['myname']
                ] = hello_message['myip']
            except KeyError:
                pass


async def listen(myip):
    proc = await asyncio.create_subprocess_exec(
        'nc', '-lk', '12345',
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    while True:
        data = await proc.stdout.readline()
        line = data.decode().rstrip()
        hello_message = json.loads(line)
        print(hello_message)
        if hello_message.get('type') == 'hello':
            try:
                ip_dict[hello_message['myname']] = hello_message['myip']
                proc.stdin.write(
                    (json.dumps({
                        'type': 'aleykumselam',
                        'myname': 'guney',
                        'myip': myip
                    }
                    ) + '\n').encode()
                )
            except KeyError:
                pass


async def send_hello(myip):
    while True:
        task_list = []
        for i in range(2, 12):
            ip = '192.168.1.' + str(i)

            if ip != myip:
                hello_task = asyncio.create_task(send_hello_to_ip(ip, myip))
                task_list.append(hello_task)

        await asyncio.gather(*task_list)
        await asyncio.sleep(5)


async def send_message():
    while True:
        print('To send a message, press M')
        print('To see the available recipient IPs, press A')
        print('To exit, press E')
        
        key = input().lower()
        if key == 'm':
            if not ip_dict:
                print('There are no available recipients. Try later.')
            else:
                print('enter recipient IP: ', end='')
                ip = input()

                print('enter your message (end it with a newline): ')
                message = input()

                proc = await asyncio.create_subprocess_exec(
                    'nc', str(ip), '12345',
                    stdout=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE
                )

                proc.stdin.write((json.dumps({
                    'type': 'hello',
                    'content': message,
                    'myip': myip
                }
                ) + '\n').encode()
                )
        elif key == 'a':
            if not ip_dict:
                print('There are no available recipients.')
            for name, ip in ip_dict.items():
                print(f'{name}: {ip}')
        elif key == 'e':
            sys.exit(0)


async def main():
    print('enter your ip: ', end='')

    global myip
    myip = input()

    listen_task = asyncio.create_task(listen(myip))
    hello_task = asyncio.create_task(send_hello(myip))
    message_task = asyncio.create_task(send_message())

    await asyncio.gather(listen_task, hello_task, message_task)


asyncio.get_event_loop().run_until_complete(main())