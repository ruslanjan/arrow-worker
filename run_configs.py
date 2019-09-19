run_configs = {
    'python': {
        'compilerScript': '/usercode/python3Compiler.sh',
        'runnerScript': '/usr/bin/python3 /usercode/file.py',
        'file': 'file.py',
        'out': '',
        'args': '',
        'lang': 'Python3',
    },
    'c++': {
        'compilerScript': '/usercode/cpp17Compiler.sh',
        'runnerScript': '/usercode/a.out',
        'file': 'file.cpp',
        'out': 'a.out',
        'args': '',
        'lang': 'C++17',
    },
    'java': {
        'compilerScript': '/usercode/java8Compiler.sh',
        'runnerScript': '/usr/lib/jvm/java-8-openjdk-amd64/bin/java Main',
        'file': 'Main.java',
        'out': '',
        'args': '',
        'lang': 'Java',
    },
}