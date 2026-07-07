#EVENTS TYPES

1. PHOTO OF FLYING DRONE IN THE SKY
2. VIDEO OF FLYING LARGE DRONE IN THE SKY
3. PHOTO OF TANK IN THE HIGHWAY
4. VIDEO OF TANK COLONY IS MOVING ACROSS THE STREET
5. PHOTO OF HEAVY TRAFFIC
6. PHOTO/VIDEO/SOUND OF AMBULANCE
7. PHOTO/VIDEO/SOUND OF FIREFIGHTER
8. EMPTY ROAD
9. EMPTY STREETS
10. SMALL TRAFFIC VIOLATION
11. EXPLOSION
11. CAR CRASH
12. NOTHING HAPPENING EVENT - I THINK WE SHOULD USE IT IN THE MODEL TO ANALYZE THAT EVERYTHING 
13. CITIZEN REPORT (HAM RADIO VOICE, HAM RADIO MAIL, PHONE APPLICATION ETC)


#SCENARIO TYPES
1. EVERYTHING IS OK
2. OCCASIONAL SMALL EVENTS
3. FLOOD (BLOCKED ROADS, AMBULANCE ETC)
4. FULL SCALE INVASION: 
    a. IRANIAN-RUSSIAN DRONE ATACK (SHAHEDS) from THE SEA and US-TERRITORY AND NORTH POLE (video, photo, sounds)
    b. TANKS WITH TROOPS ARE GOING FROM THE SOUTH TO BRITISH COLUMBIA AND ONTARIO (it case seismic activity, video, sounds etc)




#SYSTEM PIPELINE

(SOURCE0) ------->|                                                                      | -------> (EVENT 00)| AI EVENT PROCESSOR                                                  | + |   UI REPRESENTATION                                                         |
(SOURCE1) ------->|                                                                      | -------> (EVENT 01)|                                                                     | + |                                                                             |
(SOURCE2) ------->| AI SOURCE ANALYZER. MULTIMODAL                                       | -------> (EVENT 02)| TRAINED MODEL                                                       | + |   1. EVERY EVENT PUT DOTS ON THE MAP WITH DIFFERENT COLOR                   |
(SOURCE3) ------->|                                                                      | -------> (EVENT 03)| TO ANALYZE MULTIPLE EVENT BY LOCATION                               | + |   2. EVENT FEED FILLS WITH TEXT REPRESENTATION OF EVENT                     |
...               |                                                                      | -------> (EVENT 04)|                                                                     | + |   3. IF USER CLICK ON PHOTO/VIDEO/AUDIO/RF EVENT IT SHOULD HIGHLIGHT IT     |
(SOURCEN) ------->| 1. DETECT WHAT IS ON THE VIDEO/PHOTO                                 | -------> (EVENT 05)| TO PREDICT POSSIBLE OUTCOME                                         | + |     ON THE MAP OPEN POP-UP WINDOW WITH ATTACHED DATA                        |
                  | 2. DETECT WHAT IS ON THE AUDIO                                       | -------> (EVENT 06)| TO SUGGEST ACTION                                                   | + |     IF IT IS A RF PATERN -> IT SHOULD BE SHOWN AS IMAGE ON CLASSIC WATERWALL|
                  | 3. DETECT SEISMIC ACTIVITY                                           | -------> (EVENT 07)|                                                                     | + |   4.NOT SURE WHAT SHOULD BE SHOWN IN THE MIDDLE. MAYBE THINKING PROCESS?    |
                  | 4. DETECT RF PATTER TO DETECT DRONE                                  | -------> (EVENT 08)| ON DIFFERENT EVENT MAKE DECISION THAT DRONES ARE THERE              | + |     MAYBE ACTUAL SUGGESTIONS, OR POSSIBLE DIALOGUE WITH AGENT               |
                  | 5. DETECT VIDEO TRANFER TO DETECT DRONE (might be part of the (1)?)  | -------> (EVENT 09)| FOR EXAMPLE DRONE SOUND + EXPLOSION -> it means that drone attacked | + |                                                                             |
                  | 6. CHECK IF IT IS JUST CITIZEN REPORT (apply)                        | -------> (EVENT 10)|                                                                     | + |                                                                             |
                  | 7. CHECK IF TRAFFIC VIOLATION? (is it separate system?)              | -------> (EVENT NN)|                                                                     | + |                                                                             |