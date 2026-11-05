#######################################################
## Cat Tracks simulation program

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

# Simulation of bus line
import sys
import csv
from cattrack_classes import *
from cattrack_read_funcs import *

#######################################################
## Begin Simulation

#######################################################
## Set time origin--all times in minutes after this time
aclock=clock("5:00")
## Create the global variables object with # minutes to run simulation
gv=globalvars(25*60)

## Read in the stops, loads, and bus schedule
## First argument is the file name
read_stops('Bus_Stops_Times_Final.csv',gv)
read_loads('Stop_Load.csv',gv,aclock)
read_schedule('Bus_Schedule.csv',gv,aclock)

#######################################################
## Print summary of simulation components to log file
write_log("cattrack_sim.log",gv)

#######################################################
## Open files to store log of buses and stop info
f_bus=open("bus_hist.dat","w")
f_stop=open("stop_hist.dat","w")

#######################################################
## Run simulation ##
while gv.time<gv.end_time:
    ## Update buses
    for b in gv.buses:
        b.update()
    ## Update stops
    for s in gv.stops.values():
        if s.name!='SAAC':
            s.update()
    ## Print out bus and stop status every timestep
    for b in gv.buses:
        f_bus.write("%4d %s\n"%(gv.time,b.info()))
    for s in gv.stops:
        f_stop.write("%4d %s\n"%(gv.time,gv.stops[s].info()))
    gv.time+=gv.step  
f_bus.close()
f_stop.close()

#######################################################
## Write out student info
f_student=open("student.dat","w")
f_student.write("ID Status Stop Start Load Arrive Bus Route\n")
for s in gv.arrived_at_ucm:
    f_student.write("%5d %8s %5s %4d %4d %4d %8s %3s\n"%\
            (s.id,s.status,s.init_stop,s.start_time,s.load_time,s.arrival_time,s.bus,s.route))
f_student.close()

#######################################################
## Print out overal data
print("\nResults of bus simulation:")
print("Number of students arrived at stops=%d"%(gv.arrived_at_stop))
print("Number of students loaded on a bus=%d"%(gv.loaded_on_bus))
print("Number of students arrived at campus=%d"%(gv.arrived_at_campus))

    
    
