import platform
import pathlib
from bs4 import BeautifulSoup as bs

if platform.system() == 'Windows':
    topopath = '\\topo\\'
else:
    topopath = '/topo/'
packagepath = pathlib.Path(__file__).parent.parent.resolve()



def extractscale(netid, edblist):
    edblist.remove(31)
    with open(str(packagepath) + topopath + 'NETWORK_PEREGRINE_BETA_Nov142017.xml', 'r') as f:
        content = f.readlines()
        content = "".join(content)
        soup = bs(content, 'lxml')

    device = soup.find('de:device', {'netid': netid})
    board = device['instancename']
    description={}
    units={}
    scalingfactor={}
    min={}

    with open(str(packagepath) + topopath + f'DEVICE_{device["type"]}_{device["variant"]}.xml', 'r') as f:
        content = f.readlines()
        content = "".join(content)
        soup = bs(content, 'lxml')

    for edb in edblist:
        addr42 = soup.find('ep:interfaceaddress', {'addr': '42'})
        data = addr42.find('is:setting', {'id': edb})
        description[edb]= data['description']
        units[edb] = data['unit']
        min[edb] = int(data['minvalue'])
        bits = int(data['dataformat'].split('Q')[1])+1
        res = 2**bits
        '''
        apply this with following logic; 
        if min < max;
            scaled data = min + data*res
        if min > max;
            scaled data = min + (data * -res)
        '''
        scalingfactor[edb] = abs((int(data['maxvalue']) - int(data['minvalue'])))/res
        print('='*20)
        print(scalingfactor)
        if int(data['maxvalue']) < int(data['minvalue']):
            #invert this so that 'min' + scaling factor will decrement
            scalingfactor[int(f"{edb}")] = (scalingfactor[int(f"{edb}")])*-1

        # add arbitraty info for EDB 31
        description[31] = 'LLC'
        units[31] = 'SIP'
        scalingfactor[31] = 0
        min[31] = 0

    scalingfactors = dict(descriptions = description, units = units, min=min, scalingfactor = scalingfactor)

    return scalingfactors,board

'''
extractscale works on one rats file at a time... would be good to see what these formats are such that the 
steps can be determined... format will give range for output 
'''
def testcase(netid,edblist):
    output = extractscale(netid,edblist)
    print(output['scalingfactor'])

edblist = ['2','10','15','20','31']
# testcase('5',edblist)
