import argparse
import os
import platform
import struct
import sys
from datetime import datetime
from threading import Thread

import numpy as np
import pyaudio
import soundfile
import subprocess
import json
import csv
import time
import inflect
import threading
import random

p = inflect.engine()

sys.path.append(os.path.join(os.path.dirname(__file__), 'binding/python'))

from porcupine import Porcupine
from stt import recognize_input
from tts import utter_text
from recognize_face import rec_faces
import socketio

sio = socketio.Client()

CURR_INDEX = 0
ACTION_LENGTH = 0

def read_action_items():
    with open('leadership_docs/action_items.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        # action_item_count = sum(1 for row in csv_reader) - 1
        # time_per_action = round(30 / action_item_count)
        # print(time_per_action)
        owner_list = []
        action_item_list = []
        for row in csv_reader:
            if line_count != 0:
                owner = row[0]
                action_item_desc = row[1]
                owner_list.append(owner)
                action_item_list.append(action_item_desc)
            line_count += 1
        time_per_action = round(30 / (line_count-1))
        return time_per_action, owner_list, action_item_list

def move_on_next():
    global CURR_INDEX
    global ACTION_LENGTH
    global action_item_list
    global owner_list
    if CURR_INDEX < ACTION_LENGTH:
        CURR_INDEX = CURR_INDEX+1
        # text = 'The {} action item is {}. {}, do you have an update on this? '.format(p.ordinal(CURR_INDEX+1), action_item_list[CURR_INDEX], owner_list[CURR_INDEX])
        text = random_reply_gen(CURR_INDEX+1, action_item_list[CURR_INDEX], owner_list[CURR_INDEX])
        utter_text(text)
    else:
        utter_text('There are no more action items for dicussion')

def random_reply_gen(ordinal, action_item, owner):
    repl_list = [
        'The {} action item is {}. {}, do you have an update on this? '.format(p.ordinal(ordinal), action_item, owner),
        'The {} action item, {} is assigned to {}. Can you provide an update? '.format(p.ordinal(ordinal), action_item, owner),
        'The {} action item is {}. {}, any updates here? '.format(p.ordinal(ordinal), action_item, owner)
    ]
    return random.choice(repl_list)


@sio.on('connect')
def on_connect():
    global CURR_INDEX
    global ACTION_LENGTH
    global action_item_list
    global owner_list
    print('connection established')
    # faces = rec_faces()
    unit_time, owner_list, action_item_list = read_action_items()
    utter_text("Hello I am Amy. I welcome you all to this week's leadership meeting. I will be the meeting facilitator for today. Please bear with me as I am still a prototype.")
    utter_text("Based on the current list of action items, each of you would have about {} minutes to give an update on the respective action item. At any point if you are done before the specified duration just ask me to move on to the next item.".format(unit_time))

    # text = 'The {} action item is {}. {}, do you have an update on this? '.format(p.ordinal(1), action_item_list[0], owner_list[0])
    text = random_reply_gen(1, action_item_list[0], owner_list[0])
    CURR_INDEX = 0
    ACTION_LENGTH = len(action_item_list)
    utter_text(text)
    # timer = threading.Timer(6.0, move_on_next)
    # timer.start()
    # if len(faces) > 1:
    # print(faces)
    # list_att = ", ".join(faces[:-1])
    # list_lst = 'and {}'.format(faces[-1])
    # utter_text("I see that {} {} have joined today's meeting".format(list_att, list_lst))

@sio.on('bot_uttered')
def on_message(data):
    # data = json.loads(data)
    print(data)
    utter_text(data["text"])
    if data["text"] == "moving on":
        move_on_next()


@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')
    for f in os.listdir('speech_data'):
        os.remove('speech_data/{}'.format(f))

class PorcupineDemo(Thread):

    def __init__(
            self,
            library_path,
            model_file_path,
            keyword_file_paths,
            sensitivities,
            input_device_index=None,
            output_path=None):

        super(PorcupineDemo, self).__init__()

        self._library_path = library_path
        self._model_file_path = model_file_path
        self._keyword_file_paths = keyword_file_paths
        self._sensitivities = sensitivities
        self._input_device_index = input_device_index

        self._output_path = output_path
        if self._output_path is not None:
            self._recorded_frames = []

    def run(self):
        num_keywords = len(self._keyword_file_paths)

        keyword_names =\
            [os.path.basename(x).replace('.ppn', '').replace('_compressed', '').split('_')[0] for x in self._keyword_file_paths]

        print('listening for:')
        for keyword_name, sensitivity in zip(keyword_names, sensitivities):
            print('- %s (sensitivity: %f)' % (keyword_name, sensitivity))
        # Run the rasa bot
        # run_bot_cmd = "make run-socket"
        # subprocess.Popen(run_bot_cmd, shell=True)
        sio.connect('http://localhost:5005')
        # sio.wait()

        porcupine = None
        pa = None
        audio_stream = None
        try:
            porcupine = Porcupine(
                library_path=self._library_path,
                model_file_path=self._model_file_path,
                keyword_file_paths=self._keyword_file_paths,
                sensitivities=self._sensitivities)

            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
                input_device_index=self._input_device_index)

            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                if self._output_path is not None:
                    self._recorded_frames.append(pcm)

                result = porcupine.process(pcm)
                if num_keywords == 1 and result:
                    print('[%s] detected keyword' % str(datetime.now()))
                    # Start STT here
                    try:
                        user_text = recognize_input()
                        sio.emit('user_uttered', {'message': user_text})
                    except AttributeError as e:
                        pass
                elif num_keywords > 1 and result >= 0:
                    print('[%s] detected %s' % (str(datetime.now()), keyword_names[result]))

        except KeyboardInterrupt:
            print('stopping ...')
        finally:
            if porcupine is not None:
                porcupine.delete()

            if audio_stream is not None:
                audio_stream.close()

            if pa is not None:
                pa.terminate()

            if self._output_path is not None and len(self._recorded_frames) > 0:
                recorded_audio = np.concatenate(self._recorded_frames, axis=0).astype(np.int16)
                soundfile.write(self._output_path, recorded_audio, samplerate=porcupine.sample_rate, subtype='PCM_16')

    _AUDIO_DEVICE_INFO_KEYS = ['index', 'name', 'defaultSampleRate', 'maxInputChannels']

    @classmethod
    def show_audio_devices_info(cls):

        pa = pyaudio.PyAudio()

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(', '.join("'%s': '%s'" % (k, str(info[k])) for k in cls._AUDIO_DEVICE_INFO_KEYS))

        pa.terminate()


def _default_library_path():
    system = platform.system()
    machine = platform.machine()

    if system == 'Darwin':
        return os.path.join(os.path.dirname(__file__), 'lib/mac/%s/libpv_porcupine.dylib' % machine)
    elif system == 'Linux':
        if machine == 'x86_64' or machine == 'i386':
            return os.path.join(os.path.dirname(__file__), 'lib/linux/%s/libpv_porcupine.so' % machine)
        else:
            raise Exception('cannot autodetect the binary type. Please enter the path to the shared object using --library_path command line argument.')
    elif system == 'Windows':
        if platform.architecture()[0] == '32bit':
            return os.path.join(os.path.dirname(__file__), 'lib\\windows\\i686\\libpv_porcupine.dll')
        else:
            return os.path.join(os.path.dirname(__file__), 'lib\\windows\\amd64\\libpv_porcupine.dll')
    raise NotImplementedError('Porcupine is not supported on %s/%s yet!' % (system, machine))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--keyword_file_paths',
        help='comma-separated absolute paths to keyword files',
        type=str,
        default=os.path.join(os.path.dirname(__file__), 'wake-model/hey pico_windows.ppn'))

    parser.add_argument(
        '--library_path',
        help="absolute path to Porcupine's dynamic library",
        type=str,
        default=os.path.join(os.path.dirname(__file__), 'lib/windows/amd64/libpv_porcupine.dll'))

    parser.add_argument(
        '--model_file_path',
        help='absolute path to model parameter file',
        type=str,
        default=os.path.join(os.path.dirname(__file__), 'lib/common/porcupine_params.pv'))

    parser.add_argument('--sensitivities', help='detection sensitivity [0, 1]', default=0.8)
    parser.add_argument('--input_audio_device_index', help='index of input audio device', type=int, default=None)

    parser.add_argument(
        '--output_path',
        help='absolute path to where recorded audio will be stored. If not set, it will be bypassed.',
        type=str,
        default=None)

    parser.add_argument('--show_audio_devices_info', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices_info:
        PorcupineDemo.show_audio_devices_info()
    else:
        if not args.keyword_file_paths:
            raise ValueError('keyword file paths are missing')

        keyword_file_paths = [x.strip() for x in args.keyword_file_paths.split(',')]

        if isinstance(args.sensitivities, float):
            sensitivities = [args.sensitivities] * len(keyword_file_paths)
        else:
            sensitivities = [float(x) for x in args.sensitivities.split(',')]

        PorcupineDemo(
            library_path=args.library_path if args.library_path is not None else _default_library_path(),
            model_file_path=args.model_file_path,
            keyword_file_paths=keyword_file_paths,
            sensitivities=sensitivities,
            output_path=args.output_path,
            input_device_index=args.input_audio_device_index).run()
