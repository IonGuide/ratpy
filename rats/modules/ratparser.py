import pandas as pd
import rats.modules.topoparser as topo
import platform
import pathlib
import linecache
import numpy as np
from datetime import datetime
from collections import Counter
import plotly_express as px

if platform.system() == 'Windows':
    splitchar = '\\'
else:
    splitchar = '/'
packagepath = pathlib.Path(__file__).parent.parent.resolve()


class RatParse:

    def __init__(self, filename):
        self.filename = filename

    # =================================================================================================================
    # ------------------------- PACKETMARKERS FUNCTION ----------------------------------------------------------------
    # =================================================================================================================
    def packet_markers(self):
        """ Docstring.
        Determine which lines denote the start and end of each packet in the RATS files
        :return: list of integer pairs identifying on which line each packet in the file starts and ends
        """
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
                    if packetbound[1] - packetbound[0] < 2:  # assume we need at least 2 lines in packet for a full CoC
                        pass
                    else:
                        packets.append(packetbound)
        f.close()
        return packets

    # ==================================================================================================================
    # ------------------------- SAMPLERATE DETERMINATION FUNCTION ------------------------------------------------------
    # ==================================================================================================================
    def sample_rate(self, bounds, bits=16):
        """
        determine the sample rate of the rats acquisition - assume that the mode of the
        :param bounds: output from packet_markers
        :param bits: will be used in future release to affect the parsing functionality
        :return: float, determined sample rate for the RATS file
        TO DO: integrate ability to change the acceptable format for 32 bit input
        """
        samplerates = []

        # Perform operation 10 times, then determine and return the 10 results as a list
        for i in range(10):
            pack = []
            for j in range((bounds[i][1] - bounds[i][0]) + 1):
                line = linecache.getline(self.filename, bounds[i][0] + j)  # fast way to read
                line = line.strip()  # strip preceeding and tailing characters
                byts = line.split()  # split the line into bytes
                for k in byts:  # for each byte
                    pack.append(k.strip())  # append to a list for downstream processing

            lookuppack = []

            for j in range((bounds[i + 1][1] - bounds[i + 1][0]) + 1):
                line = linecache.getline(self.filename, bounds[i + 1][0] + j)  # fast way to read
                line = line.strip()  # strip preceeding and tailing characters
                byts = line.split()  # split the line into bytes
                for k in byts:  # for each byte
                    lookuppack.append(
                        k.strip())  # append to a list for downstream processing

            reftime = ''.join(lookuppack[:4])
            time = ''.join(pack[:4])

            reftime = int(reftime, 16)
            time = int(time, 16)

            duration = reftime - time

            dat = ''.join(pack[24:])
            flags = ''.join(pack[20:24])
            flags = f'{int(flags, 16):0<8b}'
            flaglist = [31 - i for i, x in enumerate(flags) if x == '1']  # generate list of flag numbers
            flaglist.reverse()  # reverse order to match data output order
            n = flaglist.index(31) + 1
            chunkdata = [dat[i:i + n * 4] for i in range(0, len(dat), n * 4)]
            samplerates.append(duration / len(chunkdata))

        c = Counter(samplerates)  # produces object to count number of elements in the list
        samplerate = c.most_common(1)[0][0]  # the most common sample rate in the dataset is likely correct one

        return samplerate

    # =================================================================================================================
    # ------------------------- PACKET PARSER -------------------------------------------------------------------------
    # =================================================================================================================
    def read_packet(self, packnum, samplerate, bounds, bits=16):
        """
        Parse a single packet from a file and return its data in the form of a pandas dataframe
        :param packnum: number of the packet to parse
        :param samplerate: output of samplerate(self) function above
        :param bounds: output of packetnumbers(self) function above
        :param bits: will be used in future releases to facilitate proper parsing
        :return: dictionary containing the information within the packet

        TO DO: integrate ability to change the acceptable format for 32 bit input
        """
        pack = []
        for i in range((bounds[packnum][1] - bounds[packnum][0]) + 1):
            line = linecache.getline(self.filename, bounds[packnum][0] + i)  # fast way to read
            line = line.strip()  # strip preceeding and tailing characters (including /n)
            byts = line.split()  # split the line into bytes
            for j in byts:  # for each byte
                pack.append(j.strip())  # append to a list for downstream processing

        # ==============================================================================================================
        #   Parse bytes as per format - may need to be updated depending on final RATS data file format
        # ==============================================================================================================
        time = ''.join(pack[:4])
        llctrigcount = ''.join(pack[4:8])
        function = ''.join(pack[8:10])
        samplenum = ''.join(pack[10:12])
        bcodehsh = ''.join(pack[12:16])
        tblnum = ''.join(pack[16:18])
        tblid = ''.join(pack[18:20])
        flags = ''.join(pack[20:24])
        dat = ''.join(pack[24:])

        # =============================================================================================================
        #   Format the outputs appropriately
        # =============================================================================================================
        flags = f'{int(flags, 16):0<8b}'  # convert flags to binary string
        flaglist = [31 - i for i, x in enumerate(flags) if x == '1']  # generate list of flag numbers
        time = int(time, 16)  # converts the time stamp into rats unitss from hex.

        flaglist.reverse()  # reverse order to match data output order
        n = flaglist.index(31) + 1  # n = EDBs which are active

        chunkdata = [dat[i:i + n * 4] for i in
                     range(0, len(dat), n * 4)]  # data is split into a single string per edb sample set

        # =============================================================================================================
        #   Construct dictionary for output
        # =============================================================================================================
        edblist = []
        datalist = []
        packetcycle = []
        timestamps = []
        scanflag = []

        numsamples = len(chunkdata)  # determine how many edb samples there are in this packet

        for i in range(numsamples):  # for every cycle, make sure that we have data for each edb
            edblist += flaglist  # every cycle will have a full complement of EDB outputs
            data = [chunkdata[i][j:j + 4] for j in range(0, len(chunkdata[i]), 4)]
            data = [int(x, 16) for x in data]  # convert data to human numbers
            datalist += data  # add the data to the list
            packetcycle += [i + 1]*len(flaglist)
            timestamps += [time + i * samplerate]*len(flaglist)
            flag = 1 if data[-1] == 1 else 0
            scanflag += [flag]*len(flaglist)  # keep a record of whether this data is interscan data or scan data

        # extending these lists now makes the later concatenation of dictionaries possible in subsequent code;
        # the dictionaries all get much bigger but the time saving facilitated by this is about 40x
        packnum = [packnum]*len(datalist)
        llctrigcount = [llctrigcount]*len(datalist)
        function = [function]*len(datalist)
        samplenum = [samplenum]*len(datalist)
        tblnum = [tblnum]*len(datalist)
        tblid = [tblid]*len(datalist)
        bcodehsh = [bcodehsh]*len(datalist)

        packetdict = dict(packet=packnum, llc=llctrigcount, function=function, sample=samplenum,
                          tablenumber=tblnum, tableid=tblid, barcodehash=bcodehsh, cycle=packetcycle,
                          scanflag=scanflag, edb=edblist, data=datalist, time=timestamps)

        # =============================================================================================================
        return packetdict

    def verifyfile(self):
        """
        Verify that the file uploaded can be processed into an acceptable format.
        Bool output facilitates the use of this function as a logic gate
        :return: bool - True if file is recognised, False if not
        """
        print('verifying that this file is a rats file')
        try:
            packetboundaries = self.packet_markers()  # should make sure that this has something to it...
            print('constructed packet boundaries')
            if len(packetboundaries) < 1:
                return False
            [x for x in packetboundaries if isinstance(x[0], int) & isinstance(x[1], int)]  # will fail if invalid
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
            # columns to verify:
            columns = ['llc', 'packet', 'cycle', 'time', 'edb', 'scanflag', 'data']
            for i in columns:
                try:
                    df[i].astype(float)
                except Exception:
                    print(f'Failed to cast column {i} of the test df to floats')
                    return False
        except Exception:
            print('File could not be verified as a RATS file')
            return False
        return True

    # =================================================================================================================
    # ------------------------- CONSTRUCT DATAFRAME FOR WHOLE FILE ----------------------------------------------------
    # =================================================================================================================
    def dataframeoutput(self):
        """
        Formalises all relevant processes in the class to produce a final dataframe to save and operate on
        :return: Dataframe containing all parsed packet data

        Run time for an ~200 mb file is < 2min
        """

        print(f'generating dataframe for {self.filename}')

        packetboundaries = self.packet_markers()  # gives us a count of the number of packets..

        samplerate = self.sample_rate(packetboundaries)
        starttime = datetime.now()

        print('ratparser is concatenating the dataframes')

        dictlist = [self.read_packet(i, samplerate=samplerate, bounds=packetboundaries)
                    for i in range(len(packetboundaries))]
        dfdict = {}

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
            df = df.drop(1,
                         level='scanflag')  # here, we drop data for all cycles which are interscan packet cycles
        except Exception:  # this was probably MRM data, one sample per packet - no interscan data
            pass

        df.index.get_level_values('function').unique()  # grab all the function numbers
        df = df.reset_index()  # flatten the dataframe ready for pivot
        pivot = pd.pivot_table(df, values='data', index=['function', 'llc'])  # pivot table for relevant info
        markers = []  # initialise markers variable
        for i in pivot.index.get_level_values(
                'function').unique().to_list():  # creates a list of all function numbers and loops over them
            mode = pivot.xs(i, level='function')['data'].mode().to_list()[
                0]  # gets the mode of the average data of the current function
            markers += pivot.xs(i, level='function').index[
                pivot.xs(i, level='function')['data'] != mode].to_list()  # wherever the average data deviates

        df['anomalous'] = df['llc'].isin(markers).astype(int)  # simple flag for anomalous data

        print('ratparser is done looking for outliers')

        # convert columns to categories for big memory savings (storage and speed)
        cols = ['packet', 'llc', 'function', 'sample', 'tablenumber', 'tableid', 'scanflag', 'anomalous', 'barcodehash']

        def catcols(dframe, columns):
            for i in columns:
                dframe[i] = dframe[i].astype('category')

            return df

        df = catcols(df, cols)

        # =============================================================================================================
        #   Scaling the data.. will import a topo parsing function, then run it on a unique list of EDBs...
        #   Want the code to rename the edbs to relevant data and scale the data values according to some factor
        # =============================================================================================================
        try:

            netid = self.filename.split(splitchar)[-1]
            netid = netid.split('.')[0]  # everything before the extension
            print(netid)
            edbs = list(df['edb'].unique())
            print(edbs)

            topodata = topo.extractscale(netid, edbs)
            print(topodata[1])

            edbdata = topodata[0]
            df.loc[:, 'min'] = df['edb'].map(edbdata['minimum'])
            df.loc[:, 'unit'] = df['edb'].map(edbdata['units'])
            df.loc[:, 'scale'] = df['edb'].map(edbdata['scalingfactor'])

            df.loc[:, 'edb'] = df['edb'].map(edbdata['descriptions'])  # replace edb with description rather than vague
            df.loc[:, 'data'] = df['min'] + (df['data'] * df['scale'])  # replace data with appropriate value
            df.loc[:, 'board'] = topodata[1]
            df['board'] = df['board'].astype('category')
        except Exception:
            df['board'] = 'NO MATCH FOUND IN TOPO FILES'

        # ==============================================================================================================
        print(f'Dataframe construction completed in: {datetime.now() - starttime}')
        print(f'dataframe for {self.filename} uses {df.memory_usage().sum() / 10e6} Mb in memory')
        print(f'HEAD OF DF PARSED FOR {file}:')
        print(df.head())

        return df


# ======================================================================================================================
# ------------------------- TEST CASE ----------------------------------------------------------------------------------
# ======================================================================================================================
def test_case(absolutepath, file, scopestart=0, scopeend=100, show=False):
    """
    Tests all aspects of the ratparser class and proves functionality by plotting relevant data
    and saving the output dataframe
    :param absolutepath: Absolute path to the RATS file
    :param file: File name of the RATS file
    :param scopestart: packet number at the lower bound of the scope plot
    :param scopeend: packet number at the upped bound of the scope plot
    :param show: bool expression to determine whether to display plots (True) or not (False)
    :return: if show is True, then 3 plot types will be displayed in the browser
    """

    try:
        df = pd.read_feather(f'../feathereddataframes/{file}.feather')
    except Exception:
        testclass = RatParse(absolutepath)
        df = testclass.dataframeoutput()
        df.to_feather(f'../feathereddataframes/{file}.feather')

    # =====================================================
    #   Scan time distributions
    # =====================================================
    def scantimeplot(dframe):
        dframe = dframe[['function', 'time', 'llc']].drop_duplicates()
        dframe = dframe.set_index('function').diff()
        dframe = dframe.reset_index()
        dframe = dframe.iloc[1:]  # the first value here will be 0, so get rid
        fig = px.violin(dframe, x='function', y='time', color='function')
        fig.update_xaxes(type='category')
        return fig

    # =====================================================
    #   Big Picture Plot
    # =====================================================
    def bigpictureplot(dframe):
        dframe = dframe[['function', 'llc', 'anomalous', 'time']].drop_duplicates()
        dframe['colours'] = np.where(dframe['anomalous'] == 0, 'blue', 'red')
        fig = px.scatter(dframe, x='time', y='function', color='colours')
        return fig

    # =====================================================
    #   Scope Plot
    # =====================================================
    def scopeplot(dframe, startpacket, endpacket):
        dframe = dframe.set_index(['llc', 'packet', 'function', 'cycle', 'time', 'edb', 'scanflag']).sort_index()
        dframe = dframe.loc[(slice(None), slice(startpacket, endpacket)), :]
        dframe = dframe.reset_index()
        fig = px.line(dframe, x='time', y='data', color='edb')
        return fig

    fig1 = scantimeplot(df)
    fig2 = bigpictureplot(df)
    fig3 = scopeplot(df, scopestart, scopeend)

    if show:
        fig1.show()
        fig2.show()
        fig3.show()


# UNCOMMENT BELOW, MODIFY PATHS AS APPROPRIATE AND RUN THIS FILE TO TEST
# ================================================
start = 10
end = 100
file = '5.txt'
# test_case(f'/users/steve/documents/workwaters/{file}',file,start,end,show=True)
