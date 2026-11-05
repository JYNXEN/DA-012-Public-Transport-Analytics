# UCM CatTracks Simulator 

![](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/cattracks.png)


## Project Status: *Active*

## Motivation
The purpose of this project is to simulate student wait times for the University of California at Merced's CatTracks bus system.

UC Merced, one of the newest University of California campuses, began accepting undergraduate students in Fall 2005. Recently, their bus transit system, CatTracks, is experiencing a number of capacity issues as students are expressing frustration about the wait and travel times to get to campus. This project attempts to simulate the impact of scaling student load on bus stop wait times.


### Methods Used
* Data Cleaning
* Exploratory Data Analysis
* Data Visualization
* Predictive Modeling


### Technologies
* Bash scripting
* Python
* Pandas
* jupyter notebook
* matplotlib


## Data & EDA
The data is primarily located in two xlxs workbooks containing ridership information from February 2019 and October 2018. Data from these months were selected since they are one of the few months during the school session in which buses run regularly and are not affected by holidays or the winter or summer breaks.

Each of these workbooks contain data on more than 12 bus lines on separate spreadsheets. As an early stage proof of concept, capacity and wait times will only be simulated for four bus lines. These lines were selected based on number of stops and weekday operation to cater to student need to take the bus to attend classes. The main goal is to gain insight on which bus stops are most affected when ridership is upscaled.
  

![Map of one of 12 bus routes to UC Merced (adapted from UCM)](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/Inked_c2_map.jpg)

The bus stop on campus is located at the Student Activities and Athletics Center (SAAC) shown in the upper-right corner of the image. The last stop before arriving to campus is Arrow Wood Drive. Since the simulation is only interested in student wait times as they travel to campus, only data associated with bus stops headed toward campus is used in the simulation.


The data was imported into pandas and cleaned. Cleaning was required since the ridership spreadsheets contained:
- inconsistent data such as variation in bus stop naming conventions between bus lines
- mispelling of bus stop names
- cells with Nan data
- random columns and rows filled with "0"
- time data of varying type
- multi-indexed data
- equivalent data between spreadsheets entered into incongruent cells


Bar graphs were made using matplotlib to explore ridership as a function of bus stop and time.

![October 2018 bus load data](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/Oct-2018-plot.png)

Plot of the monthly total of students riding the bus at particular stops according to the bus lines C1-blue, C1-gold, C2-express and G-line. The stops listed on the x-axis going from left to right are headed toward campus. The SAAC and all stops listed after SAAC are leaving campus and thus not included in the graph.

A spike in student riders is observed at Arrow Wood Drive (ARRO), the last station before students arrive on campus. Spikes are also observed at stops near residential areas: Village Apartments on "R" street (RVIL) and Compass Pointe Apartments (COMP). A spike is also observed at the bus stop near Target, which is located less than half a mile from at least six different apartment complexes.

![October 2018 bus load data](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/Oct-2018-time.png)

Plot of the monthly total of students riding the bus according to the times in which each of the individual bus lines leave the main terminal (also known as Garage). This graph shows that each of the bus routes are repeated at least a dozen times throughout the day.

Peaks in students riding the bus are observed earlier in the day which is consistent with students taking the bus to attend classes.


## Model/Simulator

The cleaned data was incorporated into a simulator developed by my partner contact at UC Merced.

Some assumptions in the model:
- students do not exit the bus until they arrive on campus.
- students are bus line agnostic and will load onto the first available bus that will take them to campus.
- student wait times are averaged according to the number of students getting on the bus at a particular stop divided by the difference in time it takes for the previous and current bus to arrive at the desired stop.
- scheduled bus stop arrival times were used and did not take into account delays.

Results of the simulation were plotted using matplotlib.

![Simulation Results 1](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/student_load.png)

![Simulation Results 2](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/waittimes2.png)


![Simulation Results 2 -- scaled](https://github.com/nlt-python/UCM_CatTracks_Simulator/blob/master/images/scaled_waittimes2.png)
## Takeaways

- statistical modeling
- writeup/reporting
- etc. (be as specific as possible)



## Featured Notebooks/Analysis/Deliverables
* [Notebook/Markdown/Slide Deck Title]
* [Notebook/Markdown/Slide DeckTitle]



### Partner
* UC Merced
* https://www.ucmerced.edu/
* Partner contact: Michael Colvin

* This work is licensed under the Creative Commons Attribution 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA. 

