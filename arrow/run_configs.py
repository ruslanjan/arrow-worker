from arrow.defaultsandbox import DefaultRunConfig

default_run_configs = {
    'python': ['usercode/file.py', DefaultRunConfig(
        prepare_script='''
                        #!/bin/bash
                        ''',
        runner_command='/usr/bin/python3 file.py',
        # file='file.py',
        description='Python3')],
    'c++': [
        'file.cpp',
        DefaultRunConfig(
            prepare_script='''
                #!/bin/bash
                g++ -std=c++17 -static -o usercode/a.out file.cpp
                ''',
            runner_command='./a.out',
            # file='file.cpp',
            description='C++17')
    ],
    # java still don't work
    # 'java': ['Main.java', DefaultRunConfig(
    #     prepare_script='''
    #                     #!/bin/bash
    #                     javac Main.java
    #                     ''',
    #     runner_command='/usr/lib/jvm/java-8-openjdk-amd64/bin/java -Xmx512M -Xss64M Main',
    #     # file='Main.java',
    #     description='Java')],
}
