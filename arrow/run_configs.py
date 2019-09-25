default_run_configs = {
    'python': [
        'usercode/file.py',
        '''
        #!/bin/bash
        ''',
        '/usr/bin/python3 file.py',
        '''
        #!/bin/bash
        printf "output@usercode/output_file\nerror_file@usercode/error_file" > payload_files 
        '''
    ],
    'c++': [
        # usercode file
        'file.cpp',
        # prepare script. saved to prepare.sh
        '''
        #!/bin/bash 
        g++ -std=c++17 -static -o usercode/a.out file.cpp 2> prepare_errors
        ''',
        # run command
        './a.out',
        # post script
        #
        '''
        #!/bin/bash
        printf "output@usercode/output_file\nerror_file@usercode/error_file" > payload_files 
        '''
    ]
}
# java still don't work
# 'java': ['Main.java', DefaultRunConfig(
#     prepare_script='''
#                     #!/bin/bash
#                     javac Main.java
#                     ''',
#     run_command='/usr/lib/jvm/java-8-openjdk-amd64/bin/java -Xmx512M -Xss64M Main',
#     # file='Main.java',
#     description='Java')],
