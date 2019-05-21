import speech_recognition as sr

def recognize_input():
    r = sr.Recognizer()
    # print(sr.Microphone.list_microphone_names())
    # sr.Microphone(device_index=3)
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('listening.....')
        audio = r.listen(source)
    try:
        interpreted_msg = r.recognize_wit(audio, key = "<wit.ai_keyhere>")
        print("You said: " + interpreted_msg)
        return interpreted_msg
    except sr.UnknownValueError:
        return 'Could not understand'
    except sr.RequestError as e:
        return "Cannot serve any requests"

if __name__ == '__main__':
    recognize_input()
