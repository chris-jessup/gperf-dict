import subprocess as sp
import sys
from cffi import FFI # To be able to link into the library

#
# gperf won't run on stdin, annoyingly
# so we need a temporary file in the filesystem
#
from tempfile import NamedTemporaryFile

class GPerfDict(object):

    def __init__(self, data: dict[str, int] | list[str]):
        if type(data) is list:
            keyvals = {key: i for i, key in enumerate(data)}
        else:
            keyvals = data

        if not self._have_gperf():
            raise ImportError("gperf appears not to be installed or not in PATH")

        if not self._have_gcc() and not self._have_clang():
            raise ImportError("gcc appears not to be installed or not in PATH")

        self.data = keyvals

        self.gperf_file = self._make_gperf_file(self.data)

        self.c_file = self._gperf_to_c(self.gperf_file)

        self.lib = self._compile_and_link(self.c_file)

    def _have_gperf(self) -> bool:
        c = sp.run(['gperf', '--version'], capture_output=True)
        return c.returncode == 0

    def _have_gcc(self) -> bool:
        c = sp.run(['gcc', '--version'], capture_output=True)
        return c.returncode == 0

    def _have_clang(self) -> bool:
        c = sp.run(['clang', '--version'], capture_output=True)
        return c.returncode == 0

    def _gperf_to_c(self, file: str) -> str:

        # When does this get cleaned up?
        # it seems to be when 
        temp_file = NamedTemporaryFile(suffix=".gperf")

        with open(temp_file.name, 'w') as fp:
            fp.write(file)

        output = sp.run(['gperf', 
                         '-L', 'ANSI-C', # Works with warnings in '-L C' 
                                         # but '-L ANSI-C' should work anywhere C89+ (ie everywhere)
                         '-C',           # Use const tables
                         '-c',           # use 'strncmp' rather than 'strcmp'
                                         # Would it be better to us '-l' which is byte comparison?
                         '-I',           # Include <string.h>
                         '--struct-type', 
                         temp_file.name], capture_output=True)

        if output.returncode == 0:
            return output.stdout

        print(output.stderr, file=sys.stderr)

    def _make_gperf_file(self, keyvals: dict[str, int]) -> str:

        lines = [
            "struct KeyVal { char *name; int val; };",
            "%%",
        ] + [key + ", " + str(val) for key,val in keyvals.items()]

        template = "\n".join(lines)

        return template


    def _compile_and_link(self, c_file):
        in_file = NamedTemporaryFile(suffix=".c")
        with open(in_file.name, "wb") as fp: fp.write(c_file)

        out_file = NamedTemporaryFile(suffix=".so")

        if self._have_gcc():
            output = sp.run(['gcc', '-shared', '-o', out_file.name, in_file.name], capture_output=True)
        else:
            # Assume clang
            output = sp.run(['clang', '-shared', '-o', out_file.name, in_file.name], capture_output=True)

        if output.returncode:
            print("Error compiling source", file=sys.stderr)
            print(output.stderr, file=sys.stderr)
            return

        ffi = FFI()
        ffi.cdef("""
            struct KeyVal { char *name; int val; };
            const struct KeyVal * in_word_set (const char *str, unsigned int len);
        """)
        return ffi.dlopen(out_file.name)

    def __contains__(self, key):
        length = len(key)
        if self.lib.in_word_set(key.encode('utf-8'), length):
            return True
        return False

    def __getitem__(self, key):
        length = len(key)
        kv = self.lib.in_word_set(key.encode('utf-8'), length)

        if not kv:
            raise KeyError(key)

        return kv.val


if __name__ == '__main__':
    g = GPerfDict(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'])

    print(g.c_file)
    print(f"FEB IN G {'feb' in g}")
    print(f"FEB IN G {g['january']=}")

    # This will raise a KeyError
    print(f"FEB IN G {g['fbe']=}")

