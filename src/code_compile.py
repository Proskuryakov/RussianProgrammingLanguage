import os
import subprocess

NET_HOME = "\"'C:\Program Files\Java\jdk-11.0.11"

JASMIN = os.path.join(NET_HOME, "bin\java.exe\" -jar \"jasmin-2.4\jasmin.jar\"")


def compile_code(code, name):
    with open(f"{name}.j", 'w') as out:
        out.write(code)
    os.system(f"{JASMIN} {name}.j")
    return f"{name}.class"


def run_java(class_name):
    return subprocess.Popen(["java", class_name, f"{class_name}.class"], stdout=subprocess.PIPE).communicate()[0].decode(
        "utf-8")
