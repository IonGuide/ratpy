#scaler will manipulate the parsed data and add to it a list of tuples, which will have units and scaling value for packet

# dataframe['scale'] = [(units, value)... (units,value)],[(units, value)... (units,value)].... etc. for now, I'll ape this


class Scaler():

    def init(self,df):
        self.df = df


    def getscalingvalues(self):
        '''
        1. get list of unique EDBs
        2. use netid to search within topo file for the type and variant of the module which produced file
        3. identify EDBs in datasheets for modules by ID property, which will be equal to edb number
        4. get name and scaling factor, store as dictionary of tuples
        5. go packetwise through dataframe and add column for scaling units and column for scaling values...

        :return:
        '''
        filename = 'some filename'
        edblist =  self.df.loc[[1]]['edblist'][1]

        units = []
        scale = []
        for i in edblist:
            units.append('V')
            scale.append(1)

        print(units)
        print(scale)

        df['']
