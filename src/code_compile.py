import os
import subprocess

JAVA_HOME = "\"'C:\\Program Files\\Java\\jdk-11.0.11"
JAVA_EXE = "\"C:\\Program Files\\Java\\jdk-11.0.11\\bin\\java.exe\""
JASMIN = os.path.join(JAVA_HOME, "bin\\java.exe\" -jar \"jasmin-2.4\\jasmin.jar\"")


def compile_code(code, name):
    with open(f"{name}.j", 'w') as out:
        out.write(code)
    os.system(f"compile_j.bat {name}.j")
    return f"{name}.class"


def run_java(class_name):
    subprocess.call(["java", class_name, f"{class_name}.class"])
