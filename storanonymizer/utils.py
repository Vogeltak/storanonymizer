import random

def gen_hex(length):
    return "".join([random.choice("0123456789ABCDEF") for i in range(length)])
