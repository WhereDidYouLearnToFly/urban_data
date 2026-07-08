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
14. ...WHAT URBAN DATA EVENTS CAN BE ADDED

#SYSTEM PIPELINE

(SOURCE0)->|              |------->|                                                                      | -------> (EVENT 00)| AI EVENT PROCESSOR                                                  | + |   UI REPRESENTATION                                                         |
(SOURCE1)->|    SOURCE    |------->|                                                                      | -------> (EVENT 01)|                                                                     | + |                                                                             |
(SOURCE2)->| STANDARTIZER |------->| AI SOURCE ANALYZER. MULTIMODAL                                       | -------> (EVENT 02)| TRAINED MODEL                                                       | + |   1. EVERY EVENT PUT DOTS ON THE MAP WITH DIFFERENT COLOR                   |
(SOURCE3)->|              |------->|                                                                      | -------> (EVENT 03)| TO ANALYZE MULTIPLE EVENT BY LOCATION                               | + |   2. EVENT FEED FILLS WITH TEXT REPRESENTATION OF EVENT                     |
...        |              |        |                                                                      | -------> (EVENT 04)|                                                                     | + |   3. IF USER CLICK ON PHOTO/VIDEO/AUDIO/RF EVENT IT SHOULD HIGHLIGHT IT     |
(SOURCEN)->|              |------->| 1. DETECT WHAT IS ON THE VIDEO/PHOTO                                 | -------> (EVENT 05)| TO PREDICT POSSIBLE OUTCOME                                         | + |     ON THE MAP OPEN POP-UP WINDOW WITH ATTACHED DATA                        |
                                   | 2. DETECT WHAT IS ON THE AUDIO                                       | -------> (EVENT 06)| TO SUGGEST ACTION                                                   | + |     IF IT IS A RF PATERN -> IT SHOULD BE SHOWN AS IMAGE ON CLASSIC WATERWALL|
                                   | 3. DETECT SEISMIC ACTIVITY                                           | -------> (EVENT 07)|                                                                     | + |   4.NOT SURE WHAT SHOULD BE SHOWN IN THE MIDDLE. MAYBE THINKING PROCESS?    |
                                   | 4. DETECT RF PATTER TO DETECT DRONE                                  | -------> (EVENT 08)| ON DIFFERENT EVENT MAKE DECISION THAT DRONES ARE THERE              | + |     MAYBE ACTUAL SUGGESTIONS, OR POSSIBLE DIALOGUE WITH AGENT               |
                                   | 5. DETECT VIDEO TRANFER TO DETECT DRONE (might be part of the (1)?)  | -------> (EVENT 09)| FOR EXAMPLE DRONE SOUND + EXPLOSION -> it means that drone attacked | + |                                                                             |
                                   | 6. CHECK IF IT IS JUST CITIZEN REPORT (apply)                        | -------> (EVENT 10)|                                                                     | + |                                                                             |
                                   | 7. CHECK IF TRAFFIC VIOLATION? (is it separate system?)              | -------> (EVENT NN)|                                                                     | + |                                                                             |


#STANDARTIZED SOURCE STRUCTURE
SINCE SOURCE CAN COMES FROM DIFFERENT SOURCE AND SYSTEM SHOULD BE FLEXIBLE FOR ADDING ADDITIONAL SOURCES WE HAVE TO DEVELOP STANDARD FOR FORMAT AND USE SOME SCRIPT/PLUGIN SYSTEM FOR NEW SOURCES TO CONVERT TO WHAT WE SHOULD HAVE

.type (fft, photo, video, audio, float sequence)
.data (binary blob)
.coordinates

(POSSIBLE STANDARTIZE WILL DO ALL REQUIRED CONVERSIONS TO THIS FORMAT)

#EVENT STRUCTURE
AI SOURCE ANALYZER WILL PROCESS IT AND WILL GENERATE EVENT STRUCTURE, THAT SHOULD BE STANDARTIZED AS WELL TO PROCESS ON AI EVENT PROCESSOR + UI SIDE

.level (0-10)
.desciption <- what was detected
.type (fft, photo, video, audio, float sequence)
.data (binary blob)
.coordinates


#DEMO FOR SPEECH. WHAT SHOULD BE CREATED

FOR DEMO THERE SHOULD BE TWO APPLICATIONS. 
FIRST ONE IS TO CONTROL SOURCE STREAM FOR DIFFERENT SCENARIOS. BASICALLY TO IMMITATE REAL-LIFE SOURCE STREAM
SECOND ONE IS ACTUALLY BE ACTUAL DEMO TO IMPRESS. THAT WILL HAVE THREE MODULES DESCRIBED ABOVE:
    1. MULTIMODAL AI SOURCE ANALYZER
    2. AI EVENT PROCESSOR
    3. UI REPRESENTATION

DUE TO LIMITATION IN TIME WE ARE ABLE TO BUILD ACTUALLY ONLY UI REPRESENTATION MODULE
(AI SOURCE ANALYZER) AND (AI EVENT PROCESSOR) SHOULD ME IMMITATED ENTIRELY OR PARTIALLY

SO, I BELIEVE "SOURCE STANDARTIZER" IS ACTUALLY WHAT WILL BE "SOURCE STREAMER" FOR THE DEMO. AND ITS OUTPUT WILL BE SOURCE EVENT WITH ADDITIONAL FIELD [PREDEFINED ANALYZE RESULT FOR AI SOURCE ANALYZER]
THEN "AI SOURCE ANALYZER" WILL USE THIS PREDEFINITION TO GENERATE "REAL LOOKING EVENT" + |META DATA TO IMMITATE AI EVENT PROCESSOR MODEL|

"REAL LOOKING EVENT" WILL BE PROCEED BY UI (TO MARK EVENT ON THE MAP, PUT IT TO THE FEED AND BE OPLE TO OPEN AND SHOW RELATED DATA)

TO IMMITATE "AI EVENT PROCESSOR" SOME META INFORMATION SHOULD BE ADDED. POSSIBLE .tag_id FIELD THAT IS LIKE (1/3, 2/3, 3/3) WHEN ALL ARE IN THEN .tag_ai_action IS CALLED THAT CAN BE MAIN EVENT/PREDICTION/SUGGETION
NEED SOME OF THEM

FOR MAIN EVENT "AI AGENT" CAN BE CREATED WITH "RESULT FROM AI EVENT PROCESSOR". NOT FOR EVERY EVENT. ONLY WHEN SOMETHING ACTUALLY DETECTED (DRONE, TANK, FLOOD, EARTHQUAKE... ETC)
FOR EACH SUCH AGENT IT IS POSSIBLE TO HAVE CONVERSATION. THIS PART MIGHT BE REAL (BASED ON OLLAMA OPENCODE GEMMA4) + CUSTOM SKILL WITH DUMMY COMMAND BUT IMITATION FOR AGENT

#DEMO SCENARIOS
1. EVERYTHING IS OK
2. OCCASIONAL SMALL EVENTS
3. FLOOD (BLOCKED ROADS, AMBULANCE ETC)
4. FULL SCALE INVASION: 
    a. IRANIAN-RUSSIAN DRONE ATACK (SHAHEDS) from THE SEA and US-TERRITORY AND NORTH POLE (video, photo, sounds)
    b. TANKS WITH TROOPS ARE GOING FROM THE SOUTH TO BRITISH COLUMBIA AND ONTARIO (it case seismic activity, video, sounds etc)




#PRESENTATION AND DOCUMENTATION

