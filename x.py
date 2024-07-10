#Import everything for the code to work

from IPython.display import display, Image, clear_output, HTML
import time
import ipywidgets as widgets
from jupyter_ui_poll import ui_events
import json
import pandas as pd
import requests 
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, db
import re 
import matplotlib.pyplot as plt

#This is the function that sends the data to the google form

def send_to_google_form(data_dict, form_url):

    '''
    This function will take in my data that i want to send tho the google and my form URL.

    The function will push the data to the google form if there are no errors 
    '''

    form_id = form_url[34:90]
    view_form_url = f'https://docs.google.com/forms/d/e/{form_id}/viewform'
    post_form_url = f'https://docs.google.com/forms/d/e/{form_id}/formResponse'

    page = requests.get(view_form_url)
    content = BeautifulSoup(page.content, "html.parser").find('script', type='text/javascript')
    content = content.text[27:-1]
    result = json.loads(content)[1][1]
    form_dict = {}
    
    loaded_all = True
    for item in result:
        if item[1] not in data_dict:
            print(f"Form item {item[1]} not found. Data not uploaded.")
            loaded_all = False
            return False
        form_dict[f'entry.{item[4][0][0]}'] = data_dict[item[1]]
    
    post_result = requests.post(post_form_url, data=form_dict)
    return post_result.ok

#This is the function that finds my firebase database

def initialize_firebase_app():
    '''
    This function checks if there is a firebase app initialized, if there isnt then a new app is initialized

    We are accessing the app through my secret key and then linking it to the firebase web URL
    '''
    
    if not firebase_admin._apps:
        cred = credentials.Certificate('bios30-7c9dc-firebase-adminsdk-tmide-ec41747b67.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://bios30-7c9dc-default-rtdb.firebaseio.com/'
        })

#This is the function that puts the data into a dict and sends it to the form

def upload_data():

    '''
    This function stores the data that i want to send to the google forms in a dictionary

    The results are pushed to the google forms as JSON data
    '''
    
    results_data = {
        'filename': ['grid1.png', 'grid1.png', 'grid1.png', 'grid1.png', 'grid1.png', 
                    'grid2.png', 'grid2.png', 'grid2.png', 'grid2.png', 'grid2.png', 
                    'grid3.png', 'grid3.png', 'grid3.png', 'grid3.png', 'grid3.png'],
        'time': times,
        'answer': answers
    }
    
    myresults = pd.DataFrame(results_data)
    results_json = myresults.to_json()
    
    
    data_dict = {
        'name': person_name,
        'gender': gender,
        'age': age,
        'percent': percent,
        'total time': total_time,
        'score': score,
        'results': results_json 
    }
    
    form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSdyr40EJWAKo_DftRRBp9YIwOL8o6RXsOzYu27ZzNBH9Slbyw/viewform?usp=sf_link'
    send_to_google_form(data_dict, form_url)

#This will await the clicking of a button

def wait_for_event(timeout=-1, interval=0.001, max_rate=20, allow_interupt=True):    
    start_wait = time.time()

    '''
    This function will wait for the event of clicking of a button
    
    Stays in a loop until the button has been clicked
    '''

    # set event info to be empty
    # as this is dict we can change entries
    # directly without using
    # the global keyword
    event_info['type'] = ""
    event_info['description'] = ""
    event_info['time'] = -1

    n_proc = int(max_rate*interval)+1
    
    with ui_events() as ui_poll:
        keep_looping = True
        while keep_looping==True:
            # process UI events
            ui_poll(n_proc)

            # end loop if we have waited more than the timeout period
            if (timeout != -1) and (time.time() > start_wait + timeout):
                keep_looping = False
                
            # end loop if event has occured
            if allow_interupt==True and event_info['description']!="":
                keep_looping = False
                
            # add pause before looping
            # to check events again
            time.sleep(interval)

#This will wait, register and then clear the output when a button is clicked

def submit_button():

    '''
    
    here the buttton is being displayed 

    then we are waiting for the clicking of the button

    upon the clicking of the button the event is registered 
    '''
    
    confirm_btn = widgets.Button(description = "Confirm")
    display(confirm_btn)
    confirm_btn.on_click(register_btn_event)
    wait_for_event()
    clear_output(wait=False)
    return

#Registers the clicking of a button

def register_btn_event(btn):

    '''
    registering the clicking of the button

    the event info for the clicking is generated

    stops the waiting for the event so the code can continue 
    '''
    
    event_info['type'] = "click"
    event_info['description'] = btn.description
    event_info['time'] = time.time()        
    return

#Registers the clicking of a button in the questions section 

def register_event(btn, correct_ans):

    '''
    function specifically for the waiting of the button click in each question 

    we are also going to update the variable correct or incorrect depending on if the person gets it correct

    globalise correct and incorrect so they can be used to calculate the score at the end
    '''

    global correct, incorrect
    
    event_info['type'] = "click"
    event_info['description'] = btn.description
    event_info['time'] = time.time()

    if btn.description == correct_ans:
        correct += 1
        answers.append(1)
    else:
        incorrect += 1
        answers.append(0)
    return

event_info = {
    'type': '',
    'description': '',
    'time': -1
}

#Calculate score of the user and display their ranking

def calculate_score():

    '''
    this function will calculate the score at the end of the test

    the score is added to the firebase database 

    data is then retrieved from the database so that the user can see how well they have done compared to others
    '''
    global percent, score

    initialize_firebase_app()
    
    clear_output(wait=False)
    
    percent = correct / (incorrect + correct) * 100
    score = percent 
    
    time_over = total_time - 90
    penalty_periods = time_over // 10
    
    for i in range(int(penalty_periods)):
        score -= 5  
    
    print(f'You got {round(percent, 1)}% in {round(total_time, 1)} seconds.')
    
    if score > 0:
        print(f'This gives you an overall score of {round(score, 1)}')
    else:
        print('You failed the test')

    ref = db.reference('scores')
    new_score_ref = ref.push({
        'score': round(score, 1),
    })

    all_scores = ref.get()
    if all_scores:

        score_list = [all_scores[key]['score'] for key in all_scores]
        score_list.sort(reverse=True)


        rank = score_list.index(round(score, 1)) + 1
        same_score_count = score_list.count(round(score, 1))
        
        if same_score_count > 1:
            print(f'Your rank: {rank} (joint), Total number of users: {len(score_list)}')
        else:
            print(f'Your rank: {rank}, Total number of users: {len(score_list)}')

#Display countdown message for user

def timer(message):

    '''
    in each question we are displaying messages that show as a count down as the test

    instead of printing multiple lines, one after the other, this function is more smooth, ie 
    the text is not being hidden and then displayed multiple times
    '''
    for i in range(3, 0, -1):
        clear_output(wait=True)
        print(message.format(i))
        time.sleep(1)
    clear_output(wait=True)

#Test part 1

def get_details():

    '''
    this function gets the details of the user

    we are getting the name, gender, age and whether or not the data is being shared

    if the person doesnt want to share their data then the data is not sent to the google form

    the user is not able to pass any of the stages of the function without entering a value
    '''

    global person_name, gender, age, consent

    display(HTML(f'<span style="font-weight: bold;">In this test you will be given 3 different grids, each grid will be shown for 20 seconds and will have 5 questions associated with it. Both speed and accuracy will be taken into account when calculating your mark</span>'))
    time.sleep(12)
    clear_output(wait=False)

    pattern = re.compile(r'^[A-Za-z]{4}$')
    
    person_name = ""
    while True:
        display(HTML(f'<span style="font-weight: bold;">Please generate your 4 letter code using the following critera: the first and second name of your childhood friend and favourite actor / actress.</span>'))
        display(HTML("<span>Input your 4 letter code here.</span>"))
        person_name = input()
        
        if pattern.match(person_name):
            clear_output(wait=True)
            break  
        else:
            clear_output(wait=True)
            display(HTML("<span style='color: red;'>Error: Incorrect code format.</span>"))
            time.sleep(1.5)
            clear_output(wait=True)  

    age = None
    while age is None:
        print('What is your age?')
        age_dropdown = widgets.Dropdown(options=[('Select Age', None)] + [(str(age), age) for age in range(18, 30)], value=None)
        display(age_dropdown)
        submit_button()
        age = age_dropdown.value

    gender_radiobuttons = widgets.RadioButtons(options=['Male', 'Female', 'Other'], description='What is your gender?', disabled=False)
    display(gender_radiobuttons)
    submit_button()
    gender = gender_radiobuttons.value

    display(HTML('Do you consent for your data to be used for the google form?')) 
    data_permission = widgets.RadioButtons(options=['Yes', 'No'], disabled=False)
    display(data_permission)
    submit_button()
    consent = data_permission.value

#Test part 2

def intro(url, message):

    '''
    this is the intro to each question 

    we are displaying an image for 20 seconds for every question
    '''
    
    print(message)
    time.sleep(1)

    timer('Image showing in {} seconds')
    
    grid1 = Image(f'{url}', width=300)
    display(grid1)
    time.sleep(20)
    clear_output(wait=False)
    time.sleep(1)
    
    timer('Test starting in {} seconds')

#Test part 3

def question(question, btn1, btn2, btn3, btn4, correct_ans):

    '''
    4 buttons are displayed for each question, if the user clicks the correct one they have got the question correct

    upon the clcking of any button, the event is registered and correct += 1 if correct and incorrect += 1 if incorrect

    the buttons are displayed as a panel

    the time taken for each question is measured
    '''

    global total_time, correct, incorrect 

    key = Image('key.png', width=1000)
    display(key)

    display(HTML(f'<span style="font-weight: bold;">{question}</span>'))
    start_time = time.time()
    
    btn1 = widgets.Button(description=btn1)
    btn2 = widgets.Button(description=btn2)
    btn3 = widgets.Button(description=btn3)
    btn4 = widgets.Button(description=btn4)

    btn1.on_click(lambda btn: register_event(btn, correct_ans)) 
    btn2.on_click(lambda btn: register_event(btn, correct_ans)) 
    btn3.on_click(lambda btn: register_event(btn, correct_ans))
    btn4.on_click(lambda btn: register_event(btn, correct_ans))

    panel = widgets.HBox([btn1, btn2, btn3, btn4])
    display(panel)

    wait_for_event()
    clear_output(wait=False)
    
    end_time = time.time()
    time_taken = end_time - start_time
    times.append(time_taken)
    total_time += time_taken
      

#Complete function for the test

correct = 0
incorrect = 0
times = []
answers = [] 
total_time = 0
score = 0
percent = 0
consent = None

def x():

    '''
    this is the complete function for the test

    before the test starts, if the user has not given consent for data usage the test is closed

    there are 3 different images displayed

    5 questions associated with each image 

    score is calculated at the end

    data is only uploaded at the end if the user gives us permission to 
    '''
    
    
    global correct, incorrect, times, answers, total_time, score, percent

    get_details()

    if consent == 'No':
        raise Exception("Consent not given. Terminating the program.")
    
    intro('grid1.png', 'Level easy')
    
    question('What was between the rectangle and triangle?', 'square', 'circle', 'cross', 'star', 'circle')
    question('What colour was the square?', 'red', 'green', 'orange', 'blue', 'red')
    question('Where was the star?', 'bottom right', 'bottom middle', 'top right', 'bottom left', 'bottom left')
    question('What was purple?', 'circle', 'cross', 'rectangle', 'square', 'rectangle')
    question('What was above the cross?', 'triangle', 'circle', 'rectangle', 'square', 'triangle')
    
    intro('grid2.png', 'Level medium')
    
    question('What was the colour of the shape in the top right?', 'pink', 'purple', 'yellow', 'red', 'yellow')
    question('What was the middle left shape?', 'triangle', 'pentagon', 'star', 'rectangle', 'triangle')
    question('Where was the pentagon?', 'top right', 'top left', 'bottom left', 'bottom right', 'top left')
    question('What was between the circle and the diamond?', 'cross', 'ellipse', 'star', 'square', 'square')
    question('How many of the shapes had rounded edges?', 'one', 'two', 'three', 'four', 'two')
    
    intro('grid3.png', 'Level hard')
    
    question('Where was the green circle?', 'bottom middle', 'bottom left', 'bottom right', 'middle right', 'bottom right')
    question('In the top left the big shape was a triangle, what was the small shape?', 'triangle', 'square', 'rectangle', 'cross', 'triangle')
    question('What colour was the central big shape?', 'blue', 'red', 'orange', 'yellow', 'yellow')
    question('What was the small shape in the middle of the big triangle and big cross?', 'pentagon', 'square', 'rectangle', 'star', 'square')
    question('Are there any cells with the two shapes being yellow and blue?','x', 'yes', 'no', 'x', 'yes')

    calculate_score()
    upload_data()








