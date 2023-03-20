# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import datetime as dt
import pandas as pd
import pytz
import numpy as np
import random
from typing import Any, Text, Dict, List
#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from pyowm import OWM #weather API
from timezonefinder import TimezoneFinder #Timezonefinder
from geopy.geocoders import Nominatim #Geographic Location of Location
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import json
import requests
#
#
#key for the weather API
key_weather = "9f6f77317e172b4aed01498eefd4ee96"

#Read the DataFrame With The Initial Information
df = pd.read_excel("Data_Teachers.xlsx")
#Rename The Columns
df.rename(columns={"Unnamed: 3": "Building", "NOMBRE": "Professor", "GRUPO ": "Department", "DESPACHO": "Room"}, inplace=True)
#Treat The Unknown Values For The Building
df['Building'] = df['Building'].fillna("Unknown")
df.dropna(axis=0, inplace=True)

#Part 1 Create List With Possible Ways User Can Refer To The Professors
out=df['Professor'].str.split(', ',expand=True)
df['Professor_First_Name']=out[1].str.strip()
#df['Professor_Last_Name']=out[0].str.split(' ').str[0]
df['Professor_Last_Name'] = out[0].str.strip()
df['Professor_First_Last_Name'] = df['Professor_First_Name'] +" "+ df['Professor_Last_Name']
df['Professor_Last_First_Name'] = df['Professor_Last_Name'] +" "+ df['Professor_First_Name']
df['Professor_Nice_Name'] = df['Professor_First_Last_Name'].str.title()

professors = []
professors = np.append(professors, df['Professor_First_Name'].values)
professors = np.append(professors, df['Professor_Last_Name'].values)
professors = np.append(professors, df['Professor_First_Last_Name'].values)
professors = np.append(professors, df['Professor_Last_First_Name'].values)
professors_list = list(professors)
professors_list = [x for x in professors_list if str(x) != 'nan']
for i in range(len(professors_list)):
    professors_list[i] = str(professors_list[i]).upper()
professors_nice_name = df['Professor_Nice_Name'].values

#Part 2 Create List With All The Rooms and The Way Hows Users Can Type Them In The Chatbot
df['Room_UP'] = df.Room.str.upper()
possible_rooms = df.Room.astype(str).unique()
df['Room_with_Dot'] = (df.Room.astype(str).str[:2]+ '.'+ df.Room.astype(str).str[2:]) #user defines room without dot
possible_rooms = np.append(possible_rooms, df['Room_with_Dot'].unique())
rooms_list = possible_rooms
#Part 3 Create List With All Ways Users Can Possibly Specify The Departments
df['Department_UP'] = df.Department.str.upper()
departments = df.Department_UP.unique()
out=df['Department_UP'].str.split(': ',expand=True)
df['Department_Full']=out[1] #Full Name Department
df['Department_Short'] = out[0] #Abbreviation Department
departments = np.append(departments, df['Department_Full'].values)
departments = np.append(departments, df['Department_Short'].values)
departments_list = departments
#Part 4 Create List With All Ways Users Can Possibly Specify The Building
df['Building_UP'] = df.Building.str.upper()


Buildings = df.Building_UP.unique()
buildings_list = Buildings

count = 0
for i in df.Room_with_Dot:
  count += 1
  try:
    j = float(i)
    j = int(j%50)

    if j == 1:
      df.Building_UP[count] = "La Nau".upper()
    elif j == 2: 
      df.Building_UP[count] = "Roc Boronat".upper()
    elif j == 3: 
      df.Building_UP[count] = "Roc Boronat".upper()
    elif j == 4: 
      df.Building_UP[count] = "Area Tallers".upper()
    elif j == 5: 
      df.Building_UP[count] = "Tanger building".upper()
    # print(df.Building_UP[count])

  except:
    df.Building_UP[count] = "Tanger building".upper()
    print("")

df['Building'] = df['Building_UP']


#Part 5 Colls of DF related to topic
prof_cols = ['Professor_First_Name','Professor_First_Last_Name','Professor_Last_First_Name','Professor_Last_Name']
department_cols = ['Department_UP','Department_Full', 'Department_Short']
room_cols = ['Room_UP', 'Room_with_Dot']
building_cols = ['Building_UP']

#Fuzzy Search Implementation
required_confidence_level = 80
def fuzzy_search(query, choices, scorer=fuzz.ratio, cutoff=45):
    results = {}
    for choice in choices:
        score = scorer(query, choice)
        if score >= cutoff:
            #results.append((choice, score))
            results[choice] = score
    return {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}

#Basic Set-Up For A Function
class ActionHelloWorld(Action):
        def name(self) -> Text:
            return "action_hello_world"
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                dispatcher.utter_message(text="Hello World!")
                return []
        
#Action That Provides The Users With The Current Time
class ActionHelloWorld(Action):
        def name(self) -> Text:
            return "action_give_time"
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                location = tracker.get_slot("location")
                location = location
                if location:
                    obj = TimezoneFinder()
                    geolocator = Nominatim(user_agent="geoapiExercises")
                    geo_location = geolocator.geocode(location)
                    timezone = obj.timezone_at(lng=geo_location.longitude, lat=geo_location.latitude)
                    time = dt.datetime.now(pytz.timezone(timezone))
                    message = f"The current time is {time} in {location}"
                else:
                    message = f"The current time is {dt.datetime.now()}"
                dispatcher.utter_message(text=message)
                return []
        
class ActionHelloWorld(Action):

     def name(self) -> Text:
         return "action_ask_weather"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                location =  tracker.get_slot("location")
                if location == None: #Slot Value Was Not Given By User
                    message =f"Sorry, I did not understand the location correctly or you forget to mention it. Could you please repeat it?."
                else:    
                    owm = OWM(key_weather)
                    mgr =owm.weather_manager()
                    observation = mgr.weather_at_place(location)
                    w = observation.weather
                    mess1= f"Weather of {location} is:"
                    mess2= f"The temperature is {w.temperature('celsius')['temp']}"
                    mess3= f"The wind speed is: {w.wind()['speed']}Km/h"
                    mess4= f"Humidity in {location} is: {w.humidity}%"
                    mess5= f"Overall Weather status is: {w.detailed_status}."

                    message = mess1 + '\n' + mess2 + '\n' +  mess3 + '\n' + mess4 + '\n' + mess5
                dispatcher.utter_message(text=message)

def jokes(f):
    
    data = requests.get(f)
    tt = json.loads(data.text)
    return tt


class ActionHelloWorld(Action):
     def name(self) -> Text:
         return "action_joke_generator"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                mess1 ="Here is a nice joke:"
                f = r"https://official-joke-api.appspot.com/random_ten"
                a = jokes(f)

                for i in (a):
                   mess2 = i["type"]
                   mess3 = i["setup"]
                   mess4 = i["punchline"]

                message = mess1 + '\n' + mess2 + '\n' +  mess3 + '\n' + mess4
                dispatcher.utter_message(text=message)
                return []
      

class ActionHelloWorld(Action):
#
        def name(self) -> Text:
            return "action_fun_fact"
#
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                fun_facts = ["Niels, his father is a farmer!", "Ferran's grandad was a farmer"]
                fun_fact = random.choice(fun_facts)
                message = f'{fun_fact}'
                dispatcher.utter_message(text=message)
                return []

class ActionHelloWorld(Action):
#
        def name(self) -> Text:
            return "action_information_professor"
#
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                prof = tracker.get_slot("professor")
                # prof = tracker.get_latest_entity_values('str')
                if prof == None: #Slot Value Was Not Given By User
                    message =f"Sorry, I did not understand the name of the professor correctly or you forget to mention his name. Can you repeat his name?."
                else:
                    prof = str(prof).upper()
                    print ("Slot Filled with", prof)
                    prof_found = False
                    if prof in professors_list: #Perfect Match
                        print ("Perfect Match")
                        df_info =  df.loc[(df[prof_cols]==prof).any(axis="columns")]
                        prof_found = True
                    else: #Not A Perfect Match Do Fuzzy Search
                        print("fuzzy search time")
                        result_fuzzy = fuzzy_search(prof, professors_list)
                        if len(result_fuzzy) == 0: #No Result Found With Fuzzy Search
                            message = (f"There is no professor found with a matching name that is working on UPF. The following professors are working on the UPF: {str(professors_nice_name)[1:-1]}")
                        else:
                            first_key = list(result_fuzzy.keys())[0]
                            if result_fuzzy[first_key] > required_confidence_level: #We are more than 80% confident about the match
                                df_info = df.loc[(df[prof_cols]==first_key.upper()).any(axis="columns")]
                                print(f"Highest confidence says that you are reffering to professor: {df_info['Professor_Nice_Name'].to_string(index=False)}.") 
                                prof_found = True
                            else: #We Found Similar Professors With Same Confidence Level But Are Not Sure About It.
                                similar_names = result_fuzzy.keys()
                                similar_names_list = df[(df.isin(similar_names).sum(axis=1))>0]['Professor_Nice_Name'].values
                                message=  (f"Sorry, I could not find the professor you were looking for. Is there any probability you were looking for one of the following professors? {str(similar_names_list[:6])[1:-1]}.")
                    #Print Information if Confident Enough About the Professors Name
                    if  prof_found == True:
                        professor = df_info["Professor_Nice_Name"].to_string(index=False)   
                        print(f"The professor is {professor}.") 
                        room = df_info["Room"].to_string(index=False)
                        department = df_info["Department"].unique()
                        print(f'The department is: {str(department.tolist())[1:-1].upper()}')
                        department_search = (department)[0]    
                        other_professors = df.loc[(df[department_cols]==department_search.upper()).any(axis="columns")]['Professor_Nice_Name'].unique().tolist()
                        if len(other_professors)>0:
                            print (other_professors)
                            other_professors.remove(professor)
                        building = df_info["Building"].to_string(index=False)
                        building = building.lower()
                        message = (f"Professor {professor} could be find in room: {room} in the {department_search} department together with {', '.join(other_professors)}. This department is located in the {building} building.")
                #message = f'{prof}'
                dispatcher.utter_message(text=message)

                return []     

class ActionHelloWorld(Action):
#
        def name(self) -> Text:
            return "action_information_department"
#
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                department =  tracker.get_slot("department")
                print(f'The department is: {department}.')
                if department == None: #Slot Value Was Not Given By User
                    message =f"Sorry, I did not understand the name of the department correctly or you forget to mention it. Could you please repeat it?."
                else:
                    department = str(department).upper()
                    print ("Slot Filled")
                    department_found = False
                    if department in departments_list: #Perfect Match
                        print ("Perfect Match")
                        df_info =  df.loc[(df[department_cols]==department).any(axis="columns")]
                        department_found = True
                    else: #Not A Perfect Match Do Fuzzy Search
                        print(f'Two Department is {department}')
                        print("fuzzy search time")
                        result_fuzzy = fuzzy_search(department, departments_list)
                        if len(result_fuzzy) == 0: #No Result Found With Fuzzy Search
                            message = (f"There is no department found with a matching name found at the UPF. The UPF has the following departments: {str(df['Department'].unique())[1:-1]}")
                        else:
                            first_key = list(result_fuzzy.keys())[0]
                            if result_fuzzy[first_key] > required_confidence_level: #We are more than 80% confident about the match
                                df_info = df.loc[(df[department_cols]==first_key.upper()).any(axis="columns")]
                                print(f"Highest confidence says that you are reffering to department: {df_info['Department'].to_string(index=False)}.") 
                                department_found = True
                            else: #We Found Similar Professors With Same Confidence Level But Are Not Sure About It.
                                similar_names = result_fuzzy.keys()
                                similar_names_list = df[(df.isin(similar_names).sum(axis=1))>0]['Department'].values
                                message=  (f"Sorry, I could not find the department you were looking for. Is there any probability you were looking for one of the following department? {str(similar_names_list)[1:-1]}.")
                    #Print Information if Confident Enough About the Professors Name
                    if  department_found == True:
                        professor = df_info["Professor_Nice_Name"].unique().tolist()
                        room = df_info["Room_with_Dot"].unique().tolist()
                        department = df_info["Department"].unique().tolist()
                        building = df_info["Building"].unique().tolist()
                        mess_prof = f"The following {len(professor)} professors are in the {', '.join(department)} department: {', '.join(professor)}."
                        mess_room = f"The {', '.join(department)} department is located in the following rooms: {', '.join(room)}."
                        mess_building = f"These rooms are located in these building(s): {', '.join(building).lower()}."
                        message = mess_building + "\n" + mess_room + "\n" + mess_prof
                dispatcher.utter_message(text=message)

                return []   
class ActionHelloWorld(Action):
#
        def name(self) -> Text:
            return "action_information_room"
#
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                room =  tracker.get_slot("room")
                print (f'Type of room is {type(room)}.')
                if room == None: #Slot Value Was Not Given By User
                    message =f"Sorry, I did not understand the name of the department correctly or you forget to mention it. Could you please repeat it?."
                else:
                    room = str(room).upper()
                    print ("Slot Filled")
                    room_found = False
                    if room in rooms_list: #Perfect Match
                        print ("Perfect Match")
                        df_info =  df.loc[(df[room_cols]==room).any(axis="columns")]
                        room_found = True
                    else: #Not A Perfect Match Do Fuzzy Search
                        print("fuzzy search time")
                        result_fuzzy = fuzzy_search(room, rooms_list)
                        if len(result_fuzzy) == 0: #No Result Found With Fuzzy Search
                            message = (f"There is no room with a matching room number found at the UPF. The UPF has the following room: {str(df['Room_with_Dot'].unique())[1:-1]}")
                        else:
                            first_key = list(result_fuzzy.keys())[0]
                            if result_fuzzy[first_key] > required_confidence_level: #We are more than 80% confident about the match
                                df_info = df.loc[(df[room_cols]==first_key.upper()).any(axis="columns")]
                                print(f"Highest confidence says that you are reffering to room: {str(df_info['Room_with_Dot'].unique())[1:-1]}.") 
                                room_found = True
                            else: #We Found Similar Professors With Same Confidence Level But Are Not Sure About It.
                                similar_names = result_fuzzy.keys()
                                similar_names_list = df[(df.isin(similar_names).sum(axis=1))>0]['Room_with_Dot'].values
                                message=  (f"Sorry, I could not find the room you were looking for. Is there any probability you were looking for one of the following room(s)? {str(similar_names_list)[1:-1]}.")
                    #Print Information if Confident Enough About the Professors Name
                    if  room_found == True:
                        professor = df_info["Professor_Nice_Name"].unique().tolist()
                        room = df_info["Room_with_Dot"].unique().tolist()
                        department = df_info["Department"].unique().tolist()
                        building = df_info["Building"].unique().tolist()
                        mess_prof = f"The following {len(professor)} professors are in the {', '.join(room)} room: {', '.join(professor)}."
                        mess_department = f"The {', '.join(room)} room is in part of the department(s) of : {', '.join(department)}."
                        #mess_room = f"The {', '.join(department)} department is located in the following rooms: {', '.join(room)}."
                        mess_building = f"The room(s) are located in these building(s): {', '.join(building)}"
                        message = mess_prof + "\n" + mess_department + "\n" + mess_building
                dispatcher.utter_message(text=message)

                return []   
        
class ActionHelloWorld(Action):
#
        def name(self) -> Text:
            return "action_information_building"
#
        def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                building =  tracker.get_slot("building")
                
                if building == None: #Slot Value Was Not Given By User
                    message =f"Sorry, I did not understand the number of the room correctly or you forget to mention it. Could you please repeat it?."
                else:
                    building = str(building).upper()
                    print ("Slot Filled")
                    building_found = False
                    if building in buildings_list: #Perfect Match
                        print ("Perfect Match")
                        df_info =  df.loc[(df[building_cols]==building).any(axis="columns")]
                        building_found = True
                    else: #Not A Perfect Match Do Fuzzy Search
                        print("fuzzy search time")
                        result_fuzzy = fuzzy_search(building, buildings_list)
                        if len(result_fuzzy) == 0: #No Result Found With Fuzzy Search
                            message = f"There is no building found with the specificied name found at the UPF. The UPF has the following building(s): {str(df['Building'].unique())[1:-1]} "
                        else:
                            first_key = list(result_fuzzy.keys())[0]
                            if result_fuzzy[first_key] > required_confidence_level: #We are more than 80% confident about the match
                                df_info = df.loc[(df[building_cols]==first_key.upper()).any(axis="columns")]
                                print(f"Highest confidence says that you are reffering to building: {df_info['Building'].to_string(index=False)}.") 
                                building_found = True
                            else: #We Found Similar Professors With Same Confidence Level But Are Not Sure About It.
                                similar_names = result_fuzzy.keys()
                                similar_names_list = df[(df.isin(similar_names).sum(axis=1))>0]['Building'].values
                                message=  (f"Sorry, I could not find the building you were looking for. Is there any probability you were looking for one of the following building(s)? {str(similar_names_list)[1:-1]}.")
                    #Print Information if Confident Enough About the Professors Name
                    if  building_found == True:
                        professor = df_info["Professor_Nice_Name"].unique().tolist()
                        room = df_info["Room_with_Dot"].unique().tolist()
                        department = df_info["Department"].unique().tolist()
                        building = df_info["Building"].unique().tolist()
                        mess_prof = f"The following {len(professor)} professors are likely to be found in {', '.join(building)} building: {', '.join(professor)}"
                        mess_room = f"The following rooms are in the {', '.join(building)} building: {', '.join(room)}"
                        #mess_building = f"The room is located in this building: {', '.join(building)}"
                        mess_department = f"The {', '.join(building)} building at UPF has the following department(s): {', '.join(department)}"
                        message = mess_department + "\n" + mess_room + "\n" + mess_prof
                dispatcher.utter_message(text=message)

                return [] 

  
#
#        def run(self, dispatcher: CollectingDispatcher,
#            tracker: Tracker,
#            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#                professor =  tracker.get_slot("location")
#                messg = f"The name of the professor is {professor}"
#                dispatcher.utter_message(text=messg)
#
#                return []
    
