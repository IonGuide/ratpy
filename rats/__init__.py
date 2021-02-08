import platform

if platform == 'Windows':
    cachepath = '\\cache'
    dfpath = '\\feathereddataframes'
    figurepath = '\\pickledfigures'
else:
    cachepath = '/cache'
    dfpath = '/feathereddataframes'
    figurepath = '/pickledfigures'

__version__ = '1.0.0.dev1'

import rats.core.rats