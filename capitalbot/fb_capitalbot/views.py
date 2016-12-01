# capitalbot/fb_capitalbot/views.py
import json, requests, random, re
from pprint import pprint

from django.views import generic
from django.http.response import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

#  ------------------------ Fill this with your page access token! -------------------------------
PAGE_ACCESS_TOKEN = "EAACVsdcb3G8BAB363RGokttaesInzPUZCPWUa1hQi5u6vVMH6YZCGPO6pmOYiVf6WAMx3VDWeis6yOPSSjKHKKXjbLVYdxv4J8JMnGUYIDa5tjOyCyQOCNXv6JV1s0XnxHOBg73keJE2ZAb47BqSJ1R9oVZBfo1115iiGoEoEwZDZD"
VERIFY_TOKEN = "795436493223"

# jokes = { 'stupid': ["""Yo' Mama is so stupid, she needs a recipe to make ice cubes.""", 
#                      """Yo' Mama is so stupid, she thinks DNA is the National Dyslexics Association."""], 
#          'fat':      ["""Yo' Mama is so fat, when she goes to a restaurant, instead of a menu, she gets an estimate.""", 
#                       """ Yo' Mama is so fat, when the cops see her on a street corner, they yell, "Hey you guys, break it up!" """], 
#          'dumb': ["""Yo' Mama is so dumb, when God was giving out brains, she thought they were milkshakes and asked for extra thick.""", 
#                   """Yo' Mama is so dumb, she locked her keys inside her motorcycle."""] }

with open('country_flag.json') as json_data:
    json_data = json.load(json_data)



countries = {}
for country in json_data:
    countries[country['name']['common'].lower()] = {"capital": country['capital'], "flag": country['flag_128'] }
  

question_number = 0
last_country = ''
max_questions = 10
num_of_right_answers = 0

# Creates answers.
def create_options():
    d = {}
    while (len(d) < 3 and len(countries) >= 4):
        country = random.choice(countries.keys())
        d[country.title()] = { "capital" : countries[country]["capital"].title(), "flag" : countries[country]["flag"] }
    pprint(d)
    return d

def create_fb_options(options):
    
    a = []

    for option in options:
        pprint(option)
        a.append({ "type" : u"postback", "title" : options[option]["capital"], "payload" : u"WRONG_CHOICE"})
    return a

def create_fb_question(fbid): 
    global last_country
    global question_number

    question_number += 1

    options = create_options()
    fb_options = create_fb_options(options)
    last_country = country = random.choice(options.keys()).title()
    capital = options[country]["capital"]
    flag = options[country]["flag"]

    # Mark the right option.
    for option in fb_options:
        if option['title'].title() == capital:
            option['payload'] = "RIGHT_CHOICE"

    request_data = json.dumps({"recipient":{"id":fbid},

    "message":{
    "attachment":{
    "type":"template",
    "payload":{
      "template_type":"generic",
      "elements":[
        {
          "title": "{}. What\'s the capital city of {}?".format(question_number, country),
          # "item_url":"https://petersfancybrownhats.com",
          "image_url":"https://raw.githubusercontent.com/cristiroma/countries/master/data/flags/" + flag,
          # "subtitle":"We\'ve got the right hat for everyone.",
          "buttons": fb_options
          
        }
      ]
    }
    }
    }})

    # question_number +=1
    return request_data

def create_fb_message(fbid, text):
    return json.dumps({"recipient":{"id":fbid},
    "message":{
        "text": text
    }})

def type_on_fb(fbid):
    return json.dumps({"recipient":{"id":fbid}, "sender_action":"typing_on"})

def send_fb(data):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=data)
    pprint(status.json())

class MessageType(object):
    MESSAGE = 'message'
    PAYLOAD = 'payload'

    CHOICES = (
        (MESSAGE, ('Message')),
        (PAYLOAD, ('Payload')),
    )


# Helper function
def post_facebook_message(fbid, recevied_message, message_type):
    global last_country
    global question_number
    global max_questions
    global num_of_right_answers
  
    if message_type is MessageType.PAYLOAD:
        if recevied_message == 'RIGHT_CHOICE':
            send_fb(create_fb_message(fbid, 'You\'re right!'))
            num_of_right_answers += 1

        else:
            send_fb(create_fb_message(fbid, 'You\'re wrong! Please find more info about ' + last_country + ':\n\n* Info: https://en.wikipedia.org/wiki/' + last_country.replace(" ", "_") + "\n\n* Location: https://www.google.co.il/maps/place/" + last_country.replace(" ", "%20") ))
            send_fb(type_on_fb(fbid))
            import time
            time.sleep(2)

        if question_number == max_questions:
            send_fb(create_fb_message(fbid, 'Your scoure is {}/{}.'.format(num_of_right_answers,max_questions)))
            if (num_of_right_answers == max_questions):
                send_fb(create_fb_message(fbid, 'Awesome! You\'re so smart! Would you marry me? \n\nFor starting a new game please type "go".'))
            else:
                send_fb(create_fb_message(fbid, 'I think you could better... \n\nFor starting a new game please type "go".'))
            question_number = 0
            num_of_right_answers = 0
        else:
            send_fb(create_fb_question(fbid))
    
    elif message_type is MessageType.MESSAGE:
        # treat start / stop

        token = re.sub(r"[^a-zA-Z0-9\s]",' ',recevied_message).lower().split()

        
        # print(token)
        if not u"go" in token:
            send_fb(create_fb_message(fbid, 'I\'m just a simple bot. I know only the word - "go".'))
        else:
            question_number = 0
            num_of_right_answers = 0
            send_fb(create_fb_question(fbid))
        
    

class CapitalBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == VERIFY_TOKEN:
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')
        
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        pprint(incoming_message)
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events 
                
                if 'message' in message:
                    post_facebook_message(message['sender']['id'], message['message']['text'], MessageType.MESSAGE)
                if 'postback' in message:
                    post_facebook_message(message['sender']['id'], message['postback']['payload'], MessageType.PAYLOAD)
        return HttpResponse()    