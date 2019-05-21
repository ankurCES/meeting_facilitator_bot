# Meeting Assitant

## Introduction
Meetings… a word we all programmers tend to hate for various reasons. Out of all the bizzare reasons that our developer brain comes up with, one is the most common – OUR MEETINGS ARE NOT TIMBOXED!!!

## Tech Stack
1.	Bot Framework – RASA
2.	Speech to Text – Wit.ai
3.	Text to Speech – Amazon Polly
4.	Backend data – AWS Aurora DB
5.	Hotword detection – Porcupine (works offline)

## High Level Flow

![alt text](https://raw.githubusercontent.com/ankurCES/meeting_facilitator_bot/master/assets/meeting_assistant_highlevel_flow.jpg)

## Steps to run

1. Install Dependencies
2. Create RASA story, nlu and domain files
3. Run RASA backend
``` 
cd rasa_data
make
```
4. Run the assistant
```
python wake_up.py
```

## Challenges 

 - The hotword detection is not proper.
 ```
 Adjust the sensitivity levels with a value between 0 and 1
 ```
 Hopefully nothing else :) 
 
## Future Plans

- Adding a face detection to mark the meeting attendance 
- Generate reports based on user activity
