'''
Module must take a dataframe, look at the filename to determine which files it needs to parse, then pull out the active EDBs
It must determine the appropriate units of that EDB and subsequently scale the output accordingly....

There must then be a page which allows interrogation of multiple scope plots from multiple tbars :s this is not trivial at all.
'''

from bs4 import BeautifulSoup as bs

def extractscale(netid, edblist):
    with open('../../../xmlfiles/NETWORK_PEREGRINE_BETA_Nov142017.xml', 'r') as f:
        content = f.readlines()
        content = "".join(content)
        soup = bs(content, 'lxml')

    device = soup.find('de:device', {'netid': netid})

    description={}
    units={}
    format={}
    min={}
    max={}

    for edb in edblist:
        with open(f'../../../xmlfiles/DEVICE_{device["type"]}_{device["variant"]}.xml', 'r') as f:
            content = f.readlines()
            content = "".join(content)
            soup = bs(content, 'lxml')

        addr42 = soup.find('ep:interfaceaddress', {'addr': '42'})
        data = addr42.find('is:setting', {'id': edb})
        description[int(f"{edb}")]= data['description']
        units[int(f"{edb}")] = data['unit']
        format[int(f"{edb}")] = data['dataformat']
        min[int(f"{edb}")] = int(data['minvalue'])
        max[int(f"{edb}")] = int(data['maxvalue'])

    scalingfactors = dict(descriptions = description, units = units, format = format, min=min, max=max)

    return scalingfactors

