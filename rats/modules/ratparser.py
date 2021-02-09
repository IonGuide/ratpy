import pandas as pd
import rats.modules.topoparser as topo
import platform
import pathlib

if platform.system() == 'Windows':
    splitchar = '\\'
else:
    splitchar = '/'
packagepath = pathlib.Path(__file__).parent.parent.resolve()

class RatParse():

    def __init__(self,filename):
        import pandas
        import numpy as np
        self.filename = filename

    # =================================================================================================================
    # ------------------------- PACKETMARKERS FUNCTION ----------------------------------------------------------------
    # =================================================================================================================
    def packet_markers(self):
        '''
        :return: list of integer pairs identifying on which line each packet in the file starts and ends
        '''
        with open(self.filename, 'r') as f:
            line = f.readline()
            totallines = 0
            while line:
                totallines += 1
                line = f.readline()
            f.seek(0)
            # list of acceptable characters for start of line
            acceptchars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
            count = 0
            packets = []

            while count < totallines:
                packetbound = []
                line = f.readline()
                count += 1
                if line[0] in acceptchars:
                    packetbound.append(count)
                    while line[0] in acceptchars:
                        line = f.readline()
                        count += 1
                        if count > totallines:
                            break
                    packetbound.append(count - 1)
                    if packetbound[1]-packetbound[0] < 2: # assume we need at least 2 lines in a packet for a full CoC
                        pass
                    else:
                        packets.append(packetbound)
        f.close()
        return packets

    # =============================================================================================================================================================================
    # ------------------------- SAMPLERATE DETERMINATION FUNCTION -----------------------------------------------------------------------------------------------------------------
    # =============================================================================================================================================================================
    def sample_rate(self,bounds, bits=16):
        '''
        determine the sample rate of the rats acquisition - assume that the mode of the
        :param bounds: output from packet_markers
        :return: float, determined sample rate for the RATS file

        TO DO: integrate ability to change the acceptable format for 32 bit input
        '''
        from collections import Counter

        samplerates = []

        # Perform operation 10 times, then determine and return the 10 results as a list
        for j in range(10):
            import linecache
            pack = []
            for i in range((bounds[j][1] - bounds[j][0]) + 1):
                line = linecache.getline(self.filename,bounds[j][0]+i)      #fast way to read
                line = line.strip()                                         #strip preceeding and tailing characters (including /n)
                bytes = line.split()                                        #split the line into bytes
                for i in bytes:                                             #for each byte
                    pack.append(i.strip())                                  #append to a list for downstream processing - saves having to deal with line reads during data extraction

            lookuppack=[]
            for i in range((bounds[j+1][1] - bounds[j+1][0]) + 1):
                line = linecache.getline(self.filename, bounds[j+1][0] + i)  # fast way to read
                line = line.strip()                                          # strip preceeding and tailing characters (including /n)
                bytes = line.split()                                         # split the line into bytes
                for i in bytes:                                              # for each byte
                    lookuppack.append(
                        i.strip())                                           # append to a list for downstream processing - saves having to deal with line reads during data extraction

            reftime = ''.join(lookuppack[:4])
            time    = ''.join(pack[:4])

            reftime = int(reftime,16)
            time = int(time,16)

            duration = reftime - time

            dat = ''.join(pack[24:])
            flags = ''.join(pack[20:24])
            flags = f'{int(flags, 16):0<8b}'
            flaglist = [31 - i for i, x in enumerate(flags) if x == '1']    # generate list of flag numbers
            flaglist.reverse()                                              # reverse order to match data output order
            n = flaglist.index(31) + 1
            chunkdata = [dat[i:i + n * 4] for i in range(0, len(dat), n * 4)]
            samplerates.append(duration / len(chunkdata))                   # add the samplerate calculated for this packet to the list.

        c = Counter(samplerates)                                            # produces object to count number of elements in the list
        samplerate = c.most_common(1)[0][0]                                 # the most common sample rate in the dataset is likely to be the correct one

        return samplerate

    # =================================================================================================================
    # ------------------------- PACKET PARSER -------------------------------------------------------------------------
    # =================================================================================================================
    def read_packet(self, packnum, samplerate, bounds, bits=16):
        '''
        Parse a single packet from a file and return its data in the form of a pandas dataframe
        :param packnum: number of the packet to parse
        :param samplerate: output of samplerate(self) function above
        :param bounds: output of packetnumbers(self) function above
        :return: dictionary containing the information within the packet

        TO DO: integrate ability to change the acceptable format for 32 bit input
        '''

        import linecache
        # using the fact that we know on which line the packet starts and stops, parse the whole thing
        pack = []
        for i in range((bounds[packnum][1] - bounds[packnum][0]) + 1):
            line = linecache.getline(self.filename,bounds[packnum][0]+i)     #fast way to read
            line = line.strip()                                     #strip preceeding and tailing characters (including /n)
            bytes = line.split()                                    #split the line into bytes
            for i in bytes:                                         #for each byte
                pack.append(i.strip())                              #append to a list for downstream processing

        #==============================================================================================================
        #   Parse bytes as per format - may need to be updated depending on final RATS data file format
        #==============================================================================================================
        #these definitions could later be pulled in from a dictionary or something with not too much trouble - remember to deal with bytes here somehow
        time            = ''.join(pack[:4])
        LLCtrigcount    = ''.join(pack[4:8])
        function        = ''.join(pack[8:10])
        samplenum       = ''.join(pack[10:12])
        bcodehsh        = ''.join(pack[12:16])
        tblnum          = ''.join(pack[16:18])
        tblid           = ''.join(pack[18:20])
        flags           = ''.join(pack[20:24])
        dat             = ''.join(pack[24:])

        # =============================================================================================================
        #   Format the outputs appropriately
        # =============================================================================================================
        flags           = f'{int(flags, 16):0<8b}'                              #convert flags to binary string
        flaglist        = [31 - i for i, x in enumerate(flags) if x == '1']     #generate list of flag numbers
        time            = int(time, 16)                                         #converts the time stamp into rats unitss from hex.

        flaglist.reverse()                                           # reverse order to match data output order
        n = flaglist.index(31)+1                                     # n here gives the number of EDBs which are active, this is then used to split out the data and determine number of cycles

        chunkdata = [dat[i:i+n*4] for i in range(0, len(dat), n*4)]  #data is split into a single string per edb sample set

        # =============================================================================================================
        #   Construct dictionary for output
        # =============================================================================================================
        edblist = []
        datalist = []
        packetcycle = []
        timestamps = []
        scanflag = []

        numSamples = len(chunkdata)                                                  # determine how many edb samples there are in this packet

        for i in range(numSamples):                                                  # for every cycle, make sure that we have data for each edb
            edblist+=flaglist                                                        # every cycle will have a full complement of EDB outputs
            data = [chunkdata[i][j:j+4] for j in range(0, len(chunkdata[i]), 4)]     # pull the full data chunk for this cycle from the list of data-per-cycle, then chop it up into 4 byte outputs, this effectively creates a list of edb outputs for this cycle
            data = [int(x, 16) for x in data]                                        # convert data to human numbers
            datalist += data                                                         # add the data to the list
            packetcycle += [i+1 for j in range(len(flaglist))]                       # make sure that each of these entries is labelled as the correct cycle
            timestamps += [time + i*samplerate for j in range(len(flaglist))]        # make sure that each of these entries has the same timestamp, as determined by the initial packet timestamp and the sample rate
            flag = 1 if data[-1]==1 else 0
            scanflag += [flag for j in range(len(flaglist))]                         # keep a record of whether this cycle of EDB data is interscan data or scan data

        # extending these lists now makes the later concatenation of dictionaries possible in subsequent code;
        # the dictionaries all get much bigger but the time saving facilitated by this is about 40x
        packnum = [packnum for i in range(len(datalist))]
        LLCtrigcount = [LLCtrigcount for i in range(len(datalist))]
        function = [function for i in range(len(datalist))]
        samplenum = [samplenum for i in range(len(datalist))]
        tblnum = [tblnum for i in range(len(datalist))]
        tblid = [tblid for i in range(len(datalist))]
        bcodehsh = [bcodehsh for i in range(len(datalist))]

        packetdict = dict(packet=packnum,llc=LLCtrigcount, function=function, sample=samplenum,
                          tablenumber=tblnum,tableid=tblid,barcodehash=bcodehsh,cycle=packetcycle,
                          scanflag=scanflag, edb=edblist,data=datalist, time = timestamps)

        # =============================================================================================================
        return packetdict


    def verifyfile(self):
        '''
        Verify that the file uploaded can be processed into an acceptable format.
        Bool output facilitates the use of this function as a logic gate
        :return: bool - True if file is recognised, False if not
        '''
        print('verifying that this file is a rats file')
        try:
            packetboundaries = self.packet_markers() #should make sure that this has something to it...
            print('constructed packet boundaries')
            if len(packetboundaries) < 1:
                return False
            [x for x in packetboundaries if isinstance(x[0], int) & isinstance(x[1], int)]
            print('Passed packetboundary test')
            samplerate = self.sample_rate(packetboundaries)
            print('Determined sample rate')
            samplerate = float(samplerate)
            print('Passed samplerate check')
            testpackets = 5 if 5 < len(packetboundaries) else len(packetboundaries)
            dictlist = [self.read_packet(i, samplerate=samplerate, bounds=packetboundaries) for i in
                            range(testpackets)]
            print('Constructed the dictionaries to verify the dataframe')
            dfdict = {}
            for listItem in dictlist:
                for key, value in listItem.items():  # Loop through all dictionary elements in the list
                    if key in list(dfdict):  # if the key already exists, append to new
                        for entry in value:
                            dfdict[key].append(entry)
                    else:  # if it's a new key, simply add to the new dictionary
                        dfdict[key] = value
            df = pd.DataFrame(dfdict)
            #columns to verify:
            columns = ['llc','packet','cycle','time','edb','scanflag','data']
            for i in columns:
                try:
                    df[i].astype(float)
                except:
                    print(f'Failed to cast column {i} of the test df to floats')
                    return False
        except:
            print('File could not be verified as a RATS file')
            return False
        return True

    # =================================================================================================================
    # ------------------------- CONSTRUCT DATAFRAME FOR WHOLE FILE ----------------------------------------------------
    # =================================================================================================================
    def dataframeoutput(self):
        '''
        Formalises all relevant processes in the class to produce a final dataframe to save and operate on
        :return: Dataframe containing all parsed packet data

        Run time for an ~200 mb file is < 2min
        '''

        print(f'generating dataframe for {self.filename}')
        from datetime import datetime

        packetboundaries = self.packet_markers() #gives us a count of the number of packets..

        samplerate = self.sample_rate(packetboundaries)
        startTime = datetime.now()

        print('ratparser is concatenating the dataframes')

        dictlist = [self.read_packet(i,samplerate=samplerate, bounds=packetboundaries)
                                        for i in range(len(packetboundaries))]
        dfdict={}

        # This code takes the list of dictionaries and stitches them into one big one, ready to transfer to a dataframe
        for listItem in dictlist:
            for key, value in listItem.items():  # Loop through all dictionary elements in the list
                if key in list(dfdict):  # if the key already exists, append to new
                    for entry in value:
                        dfdict[key].append(entry)
                else:  # if it's a new key, simply add to the new dictionary
                    dfdict[key] = value

        df = pd.DataFrame(dfdict)

        print('ratparser is done concatenating the dataframes')

        # do conversions to readable ints here
        df['llc'] = df['llc'].apply(lambda x: int(x, 16))
        df['function'] = df['function'].apply(lambda x: int(x, 16))
        df['tablenumber'] = df['tablenumber'].apply(lambda x: int(x, 16))
        df['tableid'] = df['tableid'].apply(lambda x: int(x, 16))

        # =============================================================================================================
        #   Find outliers
        # =============================================================================================================
        print('ratparser is finding outliers')
        df = df.set_index(['llc', 'packet', 'function', 'cycle', 'time', 'edb', 'scanflag']).sort_index()
        try:
            df = df.drop(1,level='scanflag') # here, we drop data for all cycles which are interscan packet cycles - these could easily be different despite the function being the same, but keep the EDB31 output in case of weird spikes in the LLC
        except:                              # this was probably MRM data, one sample per packet - no interscan data
            pass

        df.index.get_level_values('function').unique()                                                                  # grab all the function numbers
        df = df.reset_index()                                                                                           # flatten the dataframe ready for pivot
        pivot = pd.pivot_table(df, values='data', index=['function', 'llc'])                                            # pivot table for relevant info
        markers = []                                                                                                    # initialise markers variable
        for i in pivot.index.get_level_values('function').unique().to_list():                                           # creates a list of all function numbers and loops over them
            mode = pivot.xs(i, level='function')['data'].mode().to_list()[0]                                            # gets the mode of the average data of the current function
            markers += pivot.xs(i, level='function').index[pivot.xs(i, level='function')['data'] != mode].to_list()     # wherever the average data deviates

        df['anomalous'] = df['llc'].isin(markers).astype(int)                                                           # simple flag for anomalous data

        print('ratparser is done looking for outliers')

        # convert columns to categories for big memory savings (storage and speed)
        cols = ['packet', 'llc', 'function', 'sample', 'tablenumber', 'tableid', 'scanflag','anomalous','barcodehash']
        def catcols(df,cols):
            for i in cols:
                df[i] = df[i].astype('category')

            return df

        df = catcols(df,cols)

        # =============================================================================================================
        #   Scaling the data.. will import a topo parsing function, then run it on a unique list of EDBs...
        #   Want the code to rename the edbs to relevant data and scale the data values according to some factor
        # =============================================================================================================
        try:
            netid = self.filename.split('.')[0] #everything before the extension
            netid = str(netid.split(splitchar)[-1:][0])
            print(netid)
            edbs = list(df['edb'].unique())
            print(edbs)


            topodata = topo.extractscale(netid,edbs)
            print(topodata[1])

            edbdata = topodata[0]
            df.loc[:,'min'] = df['edb'].map(edbdata['min'])
            df.loc[:,'unit'] = df['edb'].map(edbdata['units'])
            df.loc[:,'scale'] = df['edb'].map(edbdata['scalingfactor'])

            df.loc[:,'edb'] = df['edb'].map(edbdata['descriptions']) # replace edb with description rather than vague
            df.loc[:,'data'] = df['min'] + (df['data']*df['scale'])  # replace data with appropriate value
            df.loc[:,'board'] = topodata[1]
            df['board'] = df['board'].astype('category')
        except:
            df['board'] = 'NO MATCH FOUND IN TOPO FILES'

        #==============================================================================================================
        print(f'Dataframe construction completed in: {datetime.now() - startTime}')
        print(f'dataframe for {self.filename} uses {df.memory_usage().sum()/10e6} Mb in memory')

        print(df.head())

        return df


#======================================================================================================================
#------------------------- TEST CASE ----------------------------------------------------------------------------------
#======================================================================================================================
def test_case(absolutepath,file,scopestart=0,scopeend=100,show=False):
    '''
    Tests all aspects of the ratparser class and proves functionality by plotting relevant data and saving the output dataframe
    :param absolutepath: Absolute path to the RATS file
    :param file: File name of the RATS file
    :param scopestart: packet number at the lower bound of the scope plot
    :param scopeend: packet number at the upped bound of the scope plot
    :param show: bool expression to determine whether to display plots (True) or not (False)
    :return: if show is True, then 3 plot types will be displayed in the browser
    '''
    import plotly_express as px

    try:
        df = pd.read_feather(f'../feathereddataframes/{file}.feather')
    except:
        testclass = RatParse(absolutepath)
        df= testclass.dataframeoutput()
        df.to_feather(f'../feathereddataframes/{file}.feather')

    # =====================================================
    #   Scan time distributions
    # =====================================================
    def scantimeplot(df):
        df = df[['function','time','llc']].drop_duplicates()
        df = df.set_index('function').diff()
        df = df.reset_index()
        df=df.iloc[1:] # the first value here will be 0 as this is a diff function which basically shifts them all in a particular direction
        fig = px.violin(df, x='function', y='time',color='function')
        fig.update_xaxes(type='category')
        return fig
    # =====================================================
    #   Big Picture Plot
    # =====================================================
    def bigpictureplot(df):

        import numpy as np
        df = df[['function', 'llc', 'anomalous', 'time']].drop_duplicates()
        df['colours'] = np.where(df['anomalous'] == 0, 'blue', 'red')
        fig = px.scatter(df, x='time', y='function', color='colours')
        return fig

    # =====================================================
    #   Scope Plot
    # =====================================================
    def scopeplot(df,startpacket,endpacket):
        df = df.set_index(['llc', 'packet', 'function', 'cycle', 'time', 'edb', 'scanflag']).sort_index()
        df = df.loc[(slice(None),slice(startpacket,endpacket)),:]
        df = df.reset_index()
        fig = px.line(df,x='time',y='data',color='edb')
        return fig


    fig1 = scantimeplot(df)
    fig2 = bigpictureplot(df)
    fig3 = scopeplot(df,scopestart,scopeend)

    if show:
        fig1.show()
        fig2.show()
        fig3.show()


def testverification(absolutepath,file):
        testclass = RatParse(absolutepath)
        if testclass.verifyfile():
            print('It looks like a RATS file')
        else:
            print('It does not look like a RATS file')


# UNCOMMENT BELOW, MODIFY PATHS AS APPROPRIATE AND RUN THIS FILE TO TEST
#================================================
scopestart = 10
scopeend = 100
file = '5.txt'
# test_case(f'/users/steve/documents/workwaters/{file}',file,scopestart,scopeend,show=True)
# testverification(f'/users/steve/documents/workwaters/{file}',file)




