from gperf_dict import GPerfDict

import random
import timeit
import time

from contextlib import contextmanager

@contextmanager
def before_after(before, after = "Done"):
    # Code to acquire resource, e.g.:
    try:
        start = time.time()
        print(before + "... ", end='', flush=True)
        yield
    finally:
        stop = time.time()
        print(after + f" [{stop-start}]", flush=True)
        print()

def read_words():

    with before_after("reading words"):
        with open('/usr/share/dict/words', 'rb') as fp:
            words = list(fp.read().splitlines())
    return words


def make_choices(words, ratio=3):

    cnt = int(ratio * (len(words)/100))

    with before_after("Choosing words"):
        choices = random.choices(words, k=cnt)
    return choices

def make_dictionaries(choices):

    with before_after("Building Gperf Dict"):
        g = GPerfDict(choices)
    with before_after("Building Normal Dict"):
        c = {choice:i for i, choice in enumerate(choices)}

    return g, c

if __name__ == '__main__':

    words = read_words()
    choices = make_choices(words, ratio=3)
    g, c = make_dictionaries(choices)

    _globals = {'g': g, 'c': c, 'words': words, 'choices': choices}
    with before_after("Running 'x in gperf_dict' test"):
        in_time_g = timeit.timeit('[word in g for word in words]', number=10, globals=_globals)
    with before_after("Running 'gperf_dict[x]' test"):
        index_time_g = timeit.timeit('[g[choice] for choice in choices]', number=10, globals=_globals)
    with before_after("Running 'x in Normal_Dict' test"):
        in_time_c = timeit.timeit('[word in c for word in words]', number=10, globals=_globals)
    with before_after("Running 'Normal_dict[x]' test"):
        index_time_c = timeit.timeit('[c[choice] for choice in choices]', number=10, globals=_globals)

    print(f"Time taken for 'x in gperf_dict': {in_time_g=}")
    print(f"Time taken for 'gperf_dict[x]': {index_time_g=}")
    print(f"Time taken for 'x in normal_dict': {in_time_c=}")
    print(f"Time taken for 'normal_dict[x]': {index_time_c=}")
    print()

