import platform
import pathlib
from bs4 import BeautifulSoup as bs

if platform.system() == 'Windows':
    topopath = '\\topo\\'
else:
    topopath = '/topo/'
packagepath = pathlib.Path(__file__).parent.parent.resolve()


def extractscale(netid, edbs):

    print("NETID")
    print(netid)
    edbs.remove(31)
    # need to organically identify the topo file
    import os
    print('FILES FOUND IN TOPO DIRECTORY:')
    try:
        for filename in os.listdir(str(packagepath) + topopath):
            print(filename)
            if 'NETWORK' in filename and 'xml' in filename:
                print("FOUND TOPOFILE")
                topofile = filename
    except Exception as e:
        print('NONE')
        print(e)


    with open(str(packagepath) + topopath + topofile, 'r') as f:
        content = f.readlines()
        content = "".join(content)
        soup = bs(content, 'lxml')

    device = soup.find('de:device', {'netid': netid})
    board = device['instancename']
    description = {}
    units = {}
    scalingfactor = {}
    minimum = {}

    with open(str(packagepath) + topopath + f'DEVICE_{device["type"]}_{device["variant"]}.xml', 'r') as f:
        content = f.readlines()
        content = "".join(content)
        soup = bs(content, 'lxml')

    for edb in edbs:
        addr42 = soup.find('ep:interfaceaddress', {'addr': '42'})
        data = addr42.find('is:setting', {'id': edb})
        description[edb] = data['description']
        units[edb] = data['unit']
        minimum[edb] = int(data['minvalue'])
        bits = int(data['dataformat'].split('Q')[1]) + 1
        res = 2 ** bits
        '''
        apply this with following logic; 
        if min < max;
            scaled data = min + data*res
        if min > max;
            scaled data = min + (data * -res)
        '''
        scalingfactor[edb] = abs((int(data['maxvalue']) - int(data['minvalue']))) / res
        if int(data['maxvalue']) < int(data['minvalue']):
            # invert this so that 'min' + scaling factor will decrement
            scalingfactor[int(f"{edb}")] = (scalingfactor[int(f"{edb}")]) * -1

        # add arbitraty info for EDB 31
        description[31] = 'LLC'
        units[31] = 'SIP'
        scalingfactor[31] = 0
        minimum[31] = 0

    scalingfactors = dict(descriptions=description, units=units, minimum=minimum, scalingfactor=scalingfactor)

    return scalingfactors, board


def testcase(netid, e):
    output = extractscale(netid, e)
    return output


edblist = ['2', '10', '15', '20', '31']
# testcase('5',edblist)
