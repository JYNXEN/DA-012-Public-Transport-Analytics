#######################################################
## Class library for Cat Tracks simulation program

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

###############################################################
## Classes
import sys

##################################################################
## Class to just hold our Global variables
class globalvars:
    def __init__(self,end_time):
        self.time=0   
        self.end_time=end_time
        ## Simulation will not work if step != 1
        self.step=1

        ## Global student counter stats
        self.student_id=0
        self.arrived_at_stop=0
        self.loaded_on_bus=0
        self.arrived_at_campus=0

        ## List of students who have arrived on campus
        self.arrived_at_ucm=[]

        ## These global dictionaries store the routes and stops by abbreviated name
        self.routes={}  
        self.stops={}
        self.loads={}

        ## List of bus objects
        self.buses=[]

## Clock class
class clock:
    def __init__(self,origin):
        self.origin_hour=int(origin.split(sep=":")[0])
        self.origin_min=int(origin.split(sep=":")[1])
        self.origin_mins=self.origin_hour*60+self.origin_min
    def minutes(self,time):
        hour=int(time.split(sep=":")[0])
        minute=int(time.split(sep=":")[1])
        mins=hour*60+minute
        if mins<self.origin_mins:
            sys.exit("Error time is less than origin time")
        return mins-self.origin_mins
    def istime(self,time):
        if len(time.split(sep=":"))!=2:
            print("Wrong number of elements in time string")
            return False
        hour=time.split(sep=":")[0].strip()
        minute=time.split(sep=":")[1].strip()
        if not hour.isdigit() or not minute.isdigit():
            print("hour or minute not digit in time")
            return False
        if not 0<=int(hour)<=23 or not 0<=int(minute)<=59:
            print("hour or minute outside correct range (0-23) or (0-59)")
            return False
        return True
    
## Load class
class load:
    def __init__(self,stop,schedule,aclock,gv):
        self.stop=stop
        self.schedule=schedule
        self.clock=aclock
        self.gv=gv
        self.times=[]
        self.loads=[]
        self.total_pred=0
        self.total_loaded=0
        self.last_interval=0
        self.loaded=0   ## Students arrived since start
        ## Unpack schedule vector to times and loads
        ipoint=0
        while schedule[ipoint].strip():
            if len(schedule)<=ipoint+1:
                sys.exit("Wrong number of entries in schedule array")
            if not self.clock.istime(schedule[ipoint]):
                sys.exit("Non time where time expected in load creator")
            self.times.append(self.clock.minutes(schedule[ipoint]))
            if not schedule[ipoint+1].strip().isdigit():
                print(schedule[ipoint+1])
                sys.exit("No numerical load value in load creator")
            self.loads.append(int(schedule[ipoint+1]))
            self.total_pred+=int(schedule[ipoint+1])
            ipoint+=2
            if ipoint >= len(schedule):
                break
        if self.loads[-1]!=0:
            sys.exit("The final load value must be zero")
    ## Print load info
    def __repr__(self):
        return "%4s %d"%(self.stop,self.total_loaded)
    def printload(self):
        print(self.__repr__)
        for i in range(len(self.times)):
            print("%4d %4d"%(self.times[i],self.loads[i]))
    ## Return number of students arriving at this time
    def load(self):
        ##If we are before the first load time return 0
        if self.gv.time<self.times[0]:
            #print("Not started")
            return 0
        ##If we are past the last time, load 0 and test total loaded
        if self.gv.time>self.times[-1]:
            #print("After last time")
            # if self.total_pred!=self.total_loaded:
            #     print("Warning--loaded at stop %s: %d not equal predicted:%d\n"%
            #           (self.stop,self.total_loaded,self.total_pred))
            return 0
        ## Determine load interval and calculate new students to add
        itime=1
        prev_loaded=0
        while self.times[itime]<self.gv.time:
            prev_loaded+=self.loads[itime-1]
            itime+=1
        if len(self.times)<itime:
            sys.exit("Too few values in times in load()")
        interval=self.times[itime]-self.times[itime-1]
        offset=self.gv.time-self.times[itime-1]
        nload=int(self.loads[itime-1]*offset/interval)
        #print(prev_loaded,interval,offset,nload)
        ## Calculate student previously loaded this interval
        loaded_interval=self.total_loaded-prev_loaded
        self.total_loaded+=nload-loaded_interval
        return nload-loaded_interval
    
## Student class
class student:
    def __init__(self,init_stop,gv):
        self.id=gv.student_id
        gv.student_id+=1
        self.status="Stop"
        self.init_stop=init_stop
        self.start_time=gv.time
        self.load_time=0
        self.arrival_time=0
        self.route="NA"
        self.bus="NA"
    def __repr__(self):
        return "ID=%5d Status=%5s Stop=%5s Start=%4d Load=%4d Arrive=%4d Bus=%7s Route=%3s\n"%\
            (self.id,self.status,self.init_stop,self.start_time,self.load_time,
             self.arrival_time,self.bus,self.route)
    def __str__(self):
        return "ID=%5d Status=%5s Stop=%5s Start=%4d Load=%4d Arrive=%4d Bus=%7s Route=%3s\n"%\
            (self.id,self.status,self.init_stop,self.start_time,self.load_time,
             self.arrival_time,self.bus,self.route)

## Bus stop class
class stop:
    def __init__(self, name, fullname,gv):
        self.name=name
        self.fullname=fullname
        self.gv=gv
        self.newstudents='Unset'  ##This will get set later
        self.students=[]
        self.history=[]
    def __repr__(self):
        return 'Stop %5s: Students=%3d'%(self.name,len(self.students))
    def __str__(self):
        return 'Stop %5s: Students=%3d'%(self.name,len(self.students))
    def printstop(self):
        print('Stop %5s: Fullname:%30s'%(self.name,self.fullname))
    def printfull(self,f_log):
        f_log.write('Stop %5s: Expected load:%4d Fullname:%40s \n'%(self.name,
                                                            self.newstudents.total_pred,
                                                            self.fullname))
    def pred_load(self):
        return self.newstudents.total_pred
    def info(self):
        return "%4s %4d"%(self.name,len(self.students))
    def update(self):
        self.history.append(len(self.students))
        ## Find current student number using load object
        new=self.newstudents.load()
        ## add new students to stop
        for i in range(new):
            self.students.append(student(self.name,self.gv))
        self.gv.arrived_at_stop+=new
        
## Route class
class route:
    def __init__(self,name,stoplist,distances,gv):
        self.name=name
        self.stops=stoplist
        self.gv=gv
        ## Build distances dictionary
        self.distances={}
        for i in range(len(stoplist)-1):
            self.distances[(stoplist[i],stoplist[i+1])]=distances[i]
        self.distances[(stoplist[-1],'GARG')]=distances[-1]
    def printroute(self):
        print("Route: %6s with %2d stops"%(self.name,len(self.stops)))
        for i in self.stops:
            self.gv.stops[i].printstop()
        print("Distances to next stop")
        for i in range(len(self.stops)-1):
            print("%4s to %4s: %2d"%(self.stops[i],self.stops[i+1],
                  self.distances[(self.stops[i],self.stops[i+1])]))
        print("%4s to %4s: %2d"%(self.stops[-1],"GARG",self.distances[(self.stops[-1],'GARG')]))
    def printfull(self,f_log):
        f_log.write("\nRoute: %6s with %2d stops\n"%(self.name,len(self.stops)))
        for i in self.stops:
            f_log.write("%4s "%self.gv.stops[i].name)
        f_log.write("\nDistances to next stop\n")
        for i in range(len(self.stops)-1):
            f_log.write("%4s to %4s: %2d\n"%(self.stops[i],self.stops[i+1],
                                           self.distances[(self.stops[i],self.stops[i+1])]))

## Bus class
class bus:
    def __init__(self, id, name, route, capacity, times, aclock, gv):
        self.id=id
        self.name=name
        self.route=route
        self.capacity=capacity
        self.times=times
        self.clock=aclock
        self.gv=gv
        ## print("gv.time=%d"%self.gv.time)
        ## convert times to minutes since origin
        self.time_mins=[]
        for i in times:
            self.time_mins.append(aclock.minutes(i))
        self.start_time=self.time_mins[0]
        self.firsttrip=True
        self.loops=len(self.time_mins)
        self.loop=0
        self.students=[]
        self.location={"stop":"GARG","offset":0,"time":0}
        self.history=[]
    def printfull(self,f_log):
        f_log.write('Bus id %d: Name: %6s Route: %8s Times: '%(self.id,self.name,self.route))
        for t in self.times:
            f_log.write("%5s "%t)
        f_log.write('\n')
    def __repr__(self):
        return 'Bus id %d: Name: %6s Loc: %6s %2d Students=%d'%(self.id,self.name,
                                                                self.location["stop"],
                                                                self.location["time"],
                                                                len(self.students))
    def __str__(self):
        return 'Bus id %d: Name: %6s Loc: %6s %2d Students=%d'%(self.id,self.name,
                                                                self.location["stop"],
                                                                self.location["time"],
                                                                len(self.students))
    def info(self):
        return "%4d %6s %4s %4d %4d "%(self.id,self.name,self.location["stop"],self.location["time"],len(self.students))
    def emptyseats(self):
        return self.capacity-len(self.students)
    def bustime(self):
        return self.gv.time
    def update(self):
        firststop=False
        self.history.append(len(self.students))
        ## If bus is still in GARG and not yet start time return
        if self.location["stop"]=="GARG" and self.start_time>self.gv.time:
            return
        ## If bus is in GARG after last loop completed return
        if self.location["stop"]=="GARG" and self.loop==self.loops:
            return
        ## If bus is in GARG, check if we've reached time to go to first stop
        ## Calculate time to first stop
        if self.location["stop"]=="GARG":
            if self.time_mins[self.loop]==self.gv.time:
                ## Set bus at first stop on route
                self.location["stop"]=self.gv.routes[self.route].stops[0]
                self.location["offset"]=0
                self.location["time"]=0  
                # print(self.__str__(),"Starting route at time",time)
                firststop=True
            else:
                ## Keep waiting until time to start next loop
                return

        if not firststop:
            ## Move bus
            self.location["time"]+=self.gv.step
            ## If bus still between stations return
            stopoffset=self.location["offset"]
            #print(self.location["offset"],self.__str__())
            traveltime=self.gv.routes[self.route].distances[(self.gv.routes[self.route].stops[stopoffset],
                                                             self.gv.routes[self.route].stops[stopoffset+1])]
            if self.location["time"]!=traveltime:
                return
            else:
                ## Put bus at next stop
                self.location["stop"]=self.gv.routes[self.route].stops[self.location["offset"]+1]
                self.location["offset"]+=1
                self.location["time"]=0
                
        ## If we got here, the bus just arrived at a stop
        ## If the stop last stop, unload and restart route
        if self.location["stop"]==self.gv.routes[self.route].stops[-1]:
            ## Unload passengers
            self.gv.arrived_at_campus+=len(self.students)
            for s in self.students:
                s.status="UCM"
                s.arrival_time=self.gv.time
                self.gv.arrived_at_ucm.append(s)
            self.students=[]
            ## Put bus in GARG and increment loop counter
            self.location["stop"]="GARG"
            self.location["time"]=0
            self.loop+=1
        else:
            ## Load passengers
            #print("Bus arrived at stop")
            waiting=len(self.gv.stops[self.location["stop"]].students)
            if waiting==0:  ## Test if stop is empty
                return
            if self.emptyseats()>=waiting:  ## Bus has room for all waiting
                for s in self.gv.stops[self.location["stop"]].students:
                    s.status="Bus_%d_%s"%(self.id,self.name)
                    s.bus="Bus_%d_%s"%(self.id,self.name)
                    s.route=self.route
                    s.load_time=self.gv.time
                    self.students.append(s)
                self.gv.stops[self.location["stop"]].students=[]
                self.gv.loaded_on_bus+=waiting
            else:
                ## Load bus
                emptyseats=self.emptyseats()
                self.gv.loaded_on_bus+=emptyseats
                for i in range(emptyseats):
                    self.gv.stops[self.location["stop"]].students[i].status="Bus_%d_%s"%(self.id,self.name)
                    self.gv.stops[self.location["stop"]].students[i].load_time=self.gv.time
                    self.gv.stops[self.location["stop"]].students[i].bus="Bus_%d_%s"%(self.id,self.name)
                    self.gv.stops[self.location["stop"]].students[i].route=self.route
                    self.students.append(self.gv.stops[self.location["stop"]].students[i])
                ## Remove students from stop
                for i in range(emptyseats):
                    self.gv.stops[self.location["stop"]].students.pop(0)

