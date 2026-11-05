import sys
import xlrd

## Create dictionary to look up stop 4-letter codes

keys={'Alexander & "G" St':'ALEX',
      'Village Apts "R" Street':'RVIL',
      'Villages Apts "M"':'MVIL',
      'Amtrak':'AMTR',
      'Arrow Wood Dr':'ARRO',
      'Arrow Wood Dr.':'ARRO',
      'Buena Vista':'BUEN',
      'Cardella & M':'CARD',
      'Cardella & M St.':'CARD',
      'Compass Pointe Apts':'COMP',
      'Compass Pointe':'COMP',
      'Cordova':'CORD',
      'El Portal Plaza':'PORT',
      'El Portal Plaza/"G" St':'PORT',
      'El Portal Plaza/"G" Street':'PORT',
      'El Redondo':'LRED',
      'Emigrant Pass':'SCHO',
      'Granville Apts':'GRAN',
      '"G" St & Alexander':"ALEX",
      'Ironstone':'IRON',
      'K 18th+19th ':'K18T',
      'M St. & Olive':'OLIV',
      'Meadows/Olivewood':'MAXX',
      'Merced College UC Parking':'MUCP',
      'Merced College':'TERM',
      'Merced Mall Target':'TARG',
      'Merced Transpo':'TRAN',
      'Mercy Hospital':'HOSP',
      'Moraga Housing':'MORA',
      'Muir Pass':'SAAC',
      'Paulson Ave & Yosemite Ave':'CORD',
      'Rite Aid/Walgreen':'RITE',
      'Scholars/Emigrant':'SCHO',
      'Scholars/Emigrant Pass':'SCHO',
      'Scholar/Emigrant':'SCHO',
      'Starbucks':'STAR',
      'Surgery Center':'SURG',
      'The Bus MCAG Office':'MCAG',
      'Tri-College/Mercy':'TRIC',
      'Tri College/Mercy':'TRIC',
      'TriCol/Mercy Hospital':'TRIC',
      'Walmart':'WALM',
      'Yosemite Church':'YOSE',
      'Gallo Rec Center':'SAAC'}

## List printing helper function for debugging
def printlist(alist):
    n=20   ## values per line
    icount=1
    for i in alist:
        print("%4d"%i,end=' ')
        if not icount%20:
            print('')
        icount+=1
    print('')
            
## Warning--this clock object is different from that in cattrack_classes.py
class clock:
    def __init__(self,origin):
        self.origin_hour=origin//100
        self.origin_min=origin%100
        self.origin_mins=self.origin_hour*60+self.origin_min
    def minutes(self,time):
        hour=time//100
        minute=time%100
        mins=hour*60+minute
        if mins<self.origin_mins:
            sys.exit("Error time is less than origin time")
        return mins-self.origin_mins
    def istime(self,time):
        hour=time//100
        minute=time%100
        if not hour.isdigit() or not minute.isdigit():
            print("hour or minute not digit in time")
            return False
        if not 0<=int(hour)<=23 or not 0<=int(minute)<=59:
            print("hour or minute outside correct range (0-23) or (0-59)")
            return False
        return True

## Define class to hold station loading info
class station_data:
    def __init__(self,key,name,line,times,loads):
        self.key=key
        self.name=name
        self.line=line
        self.times=times
        self.minutes=[aclock.minutes(time) for time in times]
        self.loads=loads
        self.timeload=[]
        self.total=0
    def calc_total(self):
        self.total=0
        for i in self.loads:
            self.total+=i
        return self.total
    def printload(self,f_load,days):
        f_load.write("%4s,5:00,"%self.key)
        for i in range(len(self.loads)):
            f_load.write("%4d, %02d:%02d,"%(int(self.loads[i]/days+.5),self.times[i]//100,self.times[i]%100))
        f_load.write("0\n")
    def printstation(self):
        self.calc_total()
        print("\n%4s %20s %5d %s"%(self.key,self.name,self.total,self.line))
        print("Times=",end='')
        for i in self.times:
            print(print_time(i),end=' ')
        print("")
        print("Loads=",end='')
        for i in self.loads:
            print("% 5d"%i,end=' ')
        print("")
    ## Merge the timelines of load and another
    def merge(self,astation):
        ## Determine which load list has final time
        # if self.times[-1] > astation.times[-1]:
        #     final_time=self.times[-1]
        # else:
        #     final_time=astation.times[-1]

        ## Lists to hold minute by minute loads
        self.timeload=[]
        ## Map self load onto minute timeload
        for t in range(self.minutes[0]+1):
            self.timeload.append(int(t*self.loads[0]/self.minutes[0]))
        offset=self.minutes[0]+1
        prev_load=self.timeload[-1]
        for i in range(len(self.loads)):
            for t in range(offset,self.minutes[i]+1):
                self.timeload.append(int(t*self.loads[i]/self.minutes[i])+prev_load)
            offset=self.minutes[i]+1
            prev_load=self.timeload[-1]

        if self.key=="ARRO":
            sum=0
            #print("Sum=",self.timeload[-1])
        ## Map astation load onto minute timeload
        astation.timeload=[]
        for t in range(astation.minutes[0]+1):
            astation.timeload.append(int(t*astation.loads[0]/astation.minutes[0]))
        offset=astation.minutes[0]+1
        prev_load=astation.timeload[-1]
        for i in range(1,len(astation.loads)):
            for t in range(offset,astation.minutes[i]+1):
                astation.timeload.append(int(t*astation.loads[i]/astation.minutes[i])+prev_load)
            offset=astation.minutes[i]+1
            prev_load=astation.timeload[-1]

        # if self.key=='ARRO':
        #     print("ARRO Self %d %d"%(len(self.timeload),self.timeload[-1]))
        #     #printlist(self.timeload)
        #     print("ARRO ASta %d %d"%(len(astation.timeload),astation.timeload[-1]))
        #     #printlist(astation.timeload)

        # print("%s and %s"%(self.key,astation.key))
        ## Combine into a single timeload--depends on relative length of timeloads
        if len(self.timeload) > len(astation.timeload):
            for i in range(len(astation.timeload)):
                self.timeload[i]+=astation.timeload[i]
            finalval=astation.timeload[-1]
            for i in range(len(astation.timeload),len(self.timeload)):
                self.timeload[i]+=finalval
            # print("Final timeload value=",self.timeload[-1])
        else:
            for i in range(len(self.timeload)):
                self.timeload[i]+=astation.timeload[i]
            offset=self.timeload[i]-astation.timeload[i]
            # print("Offset=",offset)
            for i in range(len(self.timeload),len(astation.timeload)):
                self.timeload.append(offset+astation.timeload[i])
            # print("Final timeload value=",self.timeload[-1])
                
        # if self.key=='IRON':
        #     print("IRON Comb %d:"%len(self.timeload))
        #     printlist(self.timeload)
    
        ## Map timeload back to original combined stop times
        alltimes=self.times+astation.times
        alltimes.sort()
        # print(alltimes)
        ## Give the combined times to self
        self.times=alltimes
        # if self.key=="ARRO":
        #     print("ARRO alltimes post merge")
        #     print(self.times)

        # ## Make new load schedule based on this timelist
        newloads=[]
        prev=0
        for t in alltimes:
            ##Calculate offset into timeload array
            offset=aclock.minutes(t)
            # print(offset)
            if offset>=len(self.timeload):
                print("t=%d offset=%d and len=%d"%(t,offset,len(self.timeload)))
                sys.exit("Offset into timeload too big")
            newloads.append(self.timeload[offset]-prev)
            prev=self.timeload[offset]
        self.loads=newloads
        self.minutes=[aclock.minutes(time) for time in self.times]
        
## Define function to count string occurrences in Excel row
def print_time(time):
    hours=time//100
    minutes=time%100
    return "%02d:%02d"%(hours,minutes)

def find_sixth_line(row):
    line_count=0
    count=0
    for i in range(len(row)):
        count+=1
        if row[i].ctype==1:
            row_string=row[i].value.lower()
            if row_string.count("line")==1:
                line_count+=1
                if line_count==6:
                    return count
    sys.exit("Did not find 6th count in row")

def find_total_in_row(row):
    for i in range(len(row)):
        if row[i].ctype==1:
            if row[i].value.count("TOTAL")==1:
                return True
    return False

sheets=['C1 BLUE','C1-GOLD','C2 - EXPRESS','G-Line']
#sheets=['C1 BLUE','C1-GOLD']
#sheets=['C1-GOLD','C1 BLUE']
## Set number of days in month
days=20

if len(sys.argv) > 1:
    print("Found scaling factor",float(sys.argv[1]))
    scale=float(sys.argv[1])
else:
    scale=1.0
    
aclock=clock(500)
wb=xlrd.open_workbook('219-CATTRACKS Fall 2019- February Billing.xlsx')
sheet_names=wb.sheet_names()
stations=[]
for sheet_name in sheets:
    #print(sheet_name)
    if sheet_names.count(sheet_name) != 1:
        print("sheet %s not in sheet_names"%(sheet_name))
        sys.exit()
    sheet=wb.sheet_by_name(sheet_name)

    count=0
    found_total=False
    for i in sheet.get_rows():
        if find_total_in_row(i):
            ##print("Found total in row")
            break
        count+=1
    ##print(sheet.row(count))
    count+=3
    start_col=find_sixth_line(sheet.row(count))-1
    ##Read in times
    time_count=0
    times=[]
    col=start_col+1
    while sheet.row(count)[col].ctype==2:
        times.append(int(sheet.row(count)[col].value))
        col+=1
    ##print(times)
    ## Now read in each station and the load at each time
    ## Stop when we have station name that is blank or "Total"
    nstations=0
    load_total=0
    while 1:
        load=[]
        station_name=sheet.row(count+1)[start_col].value
        if station_name=='' or station_name.lower()=='total':
            sys.exit("Error got to end of load list without finding SAAC")
        if not station_name in keys:
            print("No key for station %s"%station_name)
            sys.exit()
        ##print("station_name %s"%station_name)
        station=keys[station_name]
        if station=="SAAC":
            break
        for col in range(start_col+1,start_col+len(times)+1):
            load.append(int(sheet.row(count+1)[col].value))
            load_total+=int(sheet.row(count+1)[col].value)
        stations.append(station_data(station,station_name,sheet_name,times,load))
        nstations+=1
        count+=1
        ##print(load)
    # print("Nstations=%d"%nstations)
    # print("For line %s, load total=%d"%(sheet_name,load_total))

## Sort the stations by key
stations.sort(key=lambda x: x.key)

# for i in stations:
#     i.printstation()

## Now merge the load data from the different routes
## First merge routes with identical times
i=0
while i < len(stations)-1:
    j=i+1
    while j<len(stations):
        ## If i and j are same stop, merge j data into i
        ##print(i,j)
        if stations[i].key==stations[j].key:
            ## If the time lists are the same, just add the loads
            ## Not a very pythonic solution
            if stations[i].times==stations[j].times:
                print("Station with same schedule in 2 lines--Do not expect this to happen")
                sys.exit()
                for k in range(len(stations[i].times)):
                    stations[i].loads[k]+=stations[j].loads[k]
                stations.pop(j)
            else:
                j+=1
        else:
            j+=1
    i+=1

# for i in stations:
#     i.printstation()

i=0
while i < len(stations)-1:
    j=i+1
    while j<len(stations):
        ## If i and j are same stop, merge j data into i
        ##print(i,j)
        if stations[i].key==stations[j].key:
            if stations[i].times==stations[j].times:
                sys.exit("Exact stop matches should not happen here")
            # print("Merging %s and %s"%(stations[i].key,stations[j].key))
            # print("Sizes %d and %d"%(stations[i].calc_total(),stations[j].calc_total()))
            # print("Sizes total %d"%(stations[i].calc_total()+stations[j].calc_total()))
            premerge=stations[i].calc_total()+stations[j].calc_total()
            stations[i].merge(stations[j])
            # print("Post merge total %d"%(stations[i].calc_total()))
            if premerge!=stations[i].calc_total():
                print("Trouble premerge total=%d postmerge=%d for %s"%
                      (premerge,stations[i].calc_total(),stations[i].key))
            stations.pop(j)
        else:
            j+=1
    i+=1

## Print out Stop_Load.csv
# print("Stations after merge")
# for i in stations:
#     i.printstation()

## Create Stop_Load.csv file
f_load=open("Stop_Load.csv","w")
f_load.write("Stop, Load schedule\n")
print("Bus Stops added to Stop_Load.csv")
days/=scale
for i in stations:
    print(i.key)
    ## 23 is the number of days the load is divided by
    i.printload(f_load,days)
f_load.close()
