import atexit
import argparse
import dataclasses
import datetime
import os
import pickle
import random

from socket import *


@dataclasses.dataclass
class Cat(object):
    birthday: datetime.datetime
    name: str
    mean: bool

    @property
    def age(self) -> datetime.timedelta:
        return datetime.datetime.now()-birthday

    def meow(self):
        print(f"{self.name} says meow")

    def __repr__(self):
        r = self.__class__.__name__ + "("
        r += ", ".join([f"{k}={v}" for k, v in self.__dict__.items() if not k.startswith("_")])
        r += ")"
        return r

def gen_cats(n: int) -> [Cat]:
    names = open("./first-names.txt").read().strip().split("\n")
    cats = []
    for _ in range(n):
        cats.append(
            Cat(
                birthday=datetime.datetime.now(),
                name=" ".join([random.choice(names), random.choice(names)]),
                mean=random.random() > 0.5,
            )
        )
    return cats


def pickled_cats(n: int) -> bytes:
    return pickle.dumps(gen_cats(n))


class ProtoFlags(enum.Flag):
    MSG = 1023 # to be &'d with the msg
    CHUNK = 1024
    STOP = 2048
    HELLO = 4096 # if set password is expected
    # 8192
    # 16384
    # 32768
    # 65536
    # 131072
    # 262144
    # 524288
    # 1048576
    # 2097152
    # 4194304
    # 8388608
    # 16777216
    # 33554432
    # 67108864
    # 134217728
    # 268435456
    # 536870912
    # 1073741824
    # 2147483648

# 32       24       16       8
# /********|********|********|********\
# |                 |   HSCxxxxxxxxxxx|
# \________|________|________|________/
#
# bits 1-10 for msg len
#
# 22 flags left for control


def server():
    server = socket(AF_UNIX, SOCK_STREAM | SOCK_SEQPACKET)
    server.bind(r"./testunix")

    @atexit.register
    def _remove_socket():
        try:
            os.unlink(f"./testunix")
        except FileNotFoundError:
            pass

    server.listen()

    def handle_client(conn):
        r = conn.recv(1024)
        fbuf = int.from_bytes(r[:4])
        mbuf = r[4:]
        if fbuf & ProtoFlags.HELLO.value:
            msglen = fbuf & ProtoFlags.MSG.value
            password = pickle.loads(mbuf[:msglen])
            if password != "foo":
                conn.send(b"<GO AWAY>\n")
                conn.close()
                return
            else:
                # client accepted
                pass

        j = 10000
        pc = pickled_cats(j)
        try:
            msg = len(pc).to_bytes(2) + pc
        except OverflowError:
            chunking = True
        if chunking:
            while chunking:
        else:
        print(f"Sending {j} cats is {len(pc)} bytes!")
        conn.send(msg)
        c = int.from_bytes(conn.recv(2))
        if c == 0:
            print("Client hung up")
        else:
            print(f"Trying to receive {c} bytes")
            r = conn.recv(c)

    while True:
        client, _ = server.accept()
        handle_client(client)


def client():
    client = socket(AF_UNIX, SOCK_STREAM | SOCK_SEQPACKET)
    client.connect(r"./testunix")
    client.send(b"<HELLO>\n")
    c = int.from_bytes(client.recv(2))
    print(f"Trying to receive {c} bytes")
    r = client.recv(c)
    objs = pickle.loads(r)
    print(objs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--server", help="Run server", action="store_true")
    ap.add_argument("-c", "--client", help="Run client", action="store_true")

    args = ap.parse_args()

    if args.server:
        server()
    elif args.client:
        client()
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
