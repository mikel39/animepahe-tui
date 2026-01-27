import random
import re
import string

CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'


def get_source(p: str, a: int, c: int, k: list, _=0, d: dict = {}) -> str:
    def e(z):
        f = '' if z < a else e(int(z / a))
        z = z % a
        s = str(chr(z + 29)) if z > 35 else to_base_36(z)
        return f + s

    c -= 1
    while c > 0:
        if k[c]:
            p = re.sub(r'\b' + re.escape(e(c)) + r'\b', str(k[c]), p)
        c -= 1
    return p


def to_base_36(n):
    if n == 0:
        return '0'
    ls = []

    while n > 0:
        remainder = n % 36
        ls.append(CHARS[remainder])
        n //= 36

    return ''.join(reversed(ls))


def generate_cookie():
    # ah well
    chars = string.ascii_letters + string.digits
    random_str = ''.join(random.choice(chars) for _ in range(16))
    return {'__ddg2_': random_str}
