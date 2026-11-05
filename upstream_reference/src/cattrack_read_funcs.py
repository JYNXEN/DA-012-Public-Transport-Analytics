#######################################################
## Function library for Cat Tracks simulation program

## Developed by the Game of Life Team in the NSF-funded
## Interdisciplinary Computational Graduate Education (ICGE) program
## at UC Merced

## Team members:
## Albert Dibenedetto
## Daniel Sanchez Garrido
## Heather Stever

## Faculty mentors
## Prof. Mike Colvin
## Prof. Arnold Kim

## This work is licensed under the Creative Commons Attribution 4.0 International License.
## To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or
## send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

import csv
import sys
from cattrack_classes import *

## Read in the bus route data from CSV file
def read_stops(csv_file,gv):
    skiplines=5
    with open(csv_file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        ##Skip header lines
        for i in range(skiplines):  
            next(readCSV)

        ## Read in route line and select non-empty cells
        route_names=[]
        routelist=next(readCSV)   
        for i in routelist:
            if i.strip():
                route_names.append(i)
        nroutes=len(route_names)
        # print(route_names)

        ## Read in route data as 2D list
        data=[]
        for row in readCSV:
            data.append(row)

        ## Parse data block and create stop and route objects
        for i in range(nroutes):
            stoplist=[]
            distances=[]
            ## Read data for this route
            count=0
            # print("Reading new route")
            while True:
                fullname=data[count][i*3]
                name=data[count][i*3+1]
                distance=data[count][i*3+2]
                ##print(name)
                ##print(fullname)
                ##print(distance)
                if not name.strip() or not fullname.strip() or not distance.isdigit():
                    sys.exit("Error in reading in triplet of data for route")

                ## Add data to arrays
                ## Do we need to create a new stop object?
                if not name in gv.stops:
                    gv.stops[name]=stop(name,fullname,gv)
                stoplist.append(name)
                distances.append(int(distance))
                if name=="SAAC":
                    ## Create Route object but first check if it exists
                    if routelist[i] in gv.routes:
                        sys.exit("Error in repeated route name read in")
                    gv.routes[routelist[i]]=route(routelist[i],stoplist,distances,gv)
                    break 
                count+=1

#######################################################
## Read in schedule for student arrivals at stops (per timestep)
def read_loads(csv_file,gv,aclock):
    skiplines=1
    with open(csv_file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        ##Skip header lines
        for i in range(skiplines):  
            next(readCSV)
        for row in readCSV:
            ## Skip any totally blanks lines
            # print("Row in")
            # print(row[0])
            if not any(s.strip() for s in row):
                break
            ## Make sure first entry is a stop we recognize
            if not row[0] in gv.stops.keys():
                print(row[0])
                memo="Stop in Stop_Load.csv not recognized:%s"%row[0]
                sys.exit(memo)
            if row[0] in gv.loads.keys():
                sys.exit("Stop in Stop_Load.csv repeated ")
            schedule=row[1:]
            ## Add new load object
            # print("Creating new load object")
            #print(schedule)
            gv.loads[row[0]]=load(row[0],schedule,aclock,gv)

    ## Connect load objects to their stops
    for s in gv.stops.keys():
        # print(s)
        if s!='SAAC':
            if not s in gv.loads.keys():
                print(s)
                sys.exit("Stop with no associated load")
            gv.stops[s].newstudents=gv.loads[s]
    
def read_schedule(csv_file, gv, aclock):
    ## Read in bus data 
    skiplines=1
    bus_id=1
    with open(csv_file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        ##Skip header lines
        for i in range(skiplines):  
            next(readCSV)
        for row in readCSV:
            ## Skip any totally blanks lines
            if not any(s.strip() for s in row):
                break
            bus_name=row[0]
            bus_route=row[1]
            ## Check to make sure we know this route
            if not bus_route in gv.routes.keys():
                memo="Read in bus with unknown route: %s"%(bus_route)
                sys.exit(memo)
            bus_cap=row[2]
            if not bus_cap.isdigit():
                sys.exit("Bus capacity must be an integer")
            bus_cap=int(bus_cap)
            ##print(bus_id,bus_route,bus_cap)
            bus_times=[]
            for i in row[3:]:
                if not i.strip():
                    break
                ##print(i)
                aclock.istime(i)   ##Test if proper time
                bus_times.append(i.strip())

            ## Add new bus object
            gv.buses.append(bus(bus_id,bus_name,bus_route,bus_cap,bus_times,aclock,gv))
            bus_id+=1
        
## Write out initial log file
def write_log(log_file,gv):
    f_log=open(log_file,"w")
    f_log.write("Stops including total number of students expected:\n")
    total_pred=0
    for s in gv.stops.values():
        if s.name!='SAAC':
            s.printfull(f_log)
            total_pred+=s.pred_load()
    f_log.write("Total predicted load at all stops=%d\n"%total_pred)
    f_log.write("\nBuses, including start times:\n")
    for b in gv.buses:
        b.printfull(f_log)
    f_log.write("\nRoutes:\n")
    for r in gv.routes.values():
        r.printfull(f_log)
    f_log.close()
