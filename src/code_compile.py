import os
import subprocess

NET_HOME = "C:\Windows\Microsoft.NET\Framework\\v4.0.30319"

ILASM = os.path.join(NET_HOME, "ilasm")


def compile_code(code, filename):
    with open(filename, 'w') as out:
        out.write(code)
    os.system(f"{ILASM} /output:{filename}.prog.exe {filename}")
    return f"{filename}.prog"


def run_exe(path):
    return subprocess.Popen([path], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
