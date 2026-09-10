import os
import platform
import shutil


def retrieve_system_info():

    return {
        "operating_system": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_cores": os.cpu_count(),
        "python_version": platform.python_version(),

        "compilers": {
            "g++": shutil.which("g++"),
            "gcc": shutil.which("gcc"),
            "clang": shutil.which("clang"),
            "rustc": shutil.which("rustc"),
        }
    }