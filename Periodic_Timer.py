"""
Periodic Timer v1.0.0

A timer which plays a chosen sound at the end and loops automatically and continuously

I made this to learn more about programming with GUIs and because I needed a timer like this to help me remember to drink water (lmao).

Feel free to download, modify, and use as you wish, as long as it's for non-commercial purposes

Made with:
- PySimpleGUI v4.56.0
- pydub v0.25.1
- pygame v2.1.2
"""

import os
import pydub as dub
import pygame.mixer as mixer
from time import time
import PySimpleGUI as sg
from ast import literal_eval


# setting up config dir and file
path = f'{os.getenv("AppData")}\\Periodic_Timer'
os.makedirs(path, exist_ok=True)
if not os.path.exists(f'{path}\\config'):
    with open(f'{path}\\config', 'w') as file:
        file.write('{}')


def get_config(path):
    if os.path.exists(path):
        with open(path) as file:
            try:
                 data = literal_eval(file.read())
            except (ValueError, SyntaxError):
                return {}
    return data if type(data) is dict else {}


def main():
    # much nicer theme for your eyes
    sg.theme('DarkGray11')

    # get the config of last run, or an empty dict if the file doesn't exist or is corrupted
    CONFIG = get_config(f'{path}\\config')

    # setting up gui elements and initializing
    sbx_hrs = sg.Spin([f'{i:02d}' for i in range(10)], initial_value=CONFIG['hrs'] if 'hrs' in CONFIG else '00', key='hrs', enable_events=True, size=2)
    TXT_HRS = sg.Text('hours')
    sbx_mins = sg.Spin([f'{i:02d}' for i in range(60)], initial_value=CONFIG['mins'] if 'mins' in CONFIG else '00', key='mins', enable_events=True, size=2)
    TXT_MINS = sg.Text('minutes')
    sbx_secs = sg.Spin([f'{i:02d}' for i in range(60)], initial_value=CONFIG['secs'] if 'secs' in CONFIG else '00', key='secs', enable_events=True, size=2)
    TXT_SECS = sg.Text('seconds')
    cbx_loop = sg.CBox('Loop', default=CONFIG['loop'] if 'loop' in CONFIG else True, key='loop', enable_events=True)

    txt_timer = sg.Text('', key='timer', font='Arial 70 bold', text_color='#00a2ff', visible=False, border_width=1, relief='raised')
    btn_start = sg.Button('Start', key='start')
    btn_stop = sg.Button('Stop', key='stop', visible=False)
    btn_pause_resume = sg.Button('Pause', key='pause/resume', visible=False)

    btn_browse = sg.FileBrowse('Choose your alarm', initial_folder=os.path.dirname(CONFIG['audio_path']) if 'audio_path' in CONFIG else os.getenv('USERPROFILE'), file_types=(('Audio Files', '*.mp3 *.wav *.ogg *.aac *.mp2 *.oga *.aiff'),), key='browse', target='audio_path')
    txt_audio_path = sg.Text(text=CONFIG['audio_path'] if 'audio_path' in CONFIG else '', expand_x=True, key='audio_path')

    sli_volume = sg.Slider(key='volume', range=(-30, 15), default_value=CONFIG['volume'] if 'volume' in CONFIG else 0, resolution=1, orientation='h', disable_number_display=True, enable_events=True, expand_x=True)
    txt_current_volume = sg.Text(text=int(sli_volume.DefaultValue) if sli_volume.DefaultValue < 0 else f'+{int(sli_volume.DefaultValue)}', size=3, key='current_volume')
    TXT_LABEL_VOLUME = sg.Text(text='Volume', key='label_volume')

    LAYOUT = [
        [sbx_hrs, TXT_HRS, sbx_mins, TXT_MINS, sbx_secs, TXT_SECS, cbx_loop, sg.Push()],
        [sg.Column([[TXT_LABEL_VOLUME, txt_current_volume, sli_volume], [sg.pin(txt_timer)]]), sg.vbottom(sg.Column([[btn_start, btn_stop, btn_pause_resume]]))],
        [sg.pin(btn_browse), txt_audio_path],
        ]
    window = sg.Window('Periodic Timer', LAYOUT, finalize=True)
    mixer.init()

    # window go brrr
    while not window.was_closed():
        event, value = window.read()

        # display updating
        if event != sg.WIN_CLOSED:
            window['hrs'](value=f'{int(value["hrs"]):02d}')
            window['mins'](value=f'{int(value["mins"]):02d}')
            window['secs'](value=f'{int(value["secs"]):02d}')

        if event == 'volume':
            window['current_volume'](value=int(value['volume']) if value['volume'] < 0 else f'+{int(value["volume"])}')

        elif event == 'start' and (int(value['hrs']) or int(value['mins']) or int(value['secs'])):
            # updating layout
            window['hrs'](disabled=True)
            window['mins'](disabled=True)
            window['secs'](disabled=True)
            window['loop'](disabled=True)
            window['browse'](disabled=True)
            window['start'](visible=False)
            window['stop'](visible=True)
            window['pause/resume'](visible=True)
            window.refresh()  # refresh before showing timer so timer only shows once it starts running
            window['timer'](value=f'{value["hrs"]}:{value["mins"]}:{value["secs"]}', visible=True)

            # setting up audio
            volume = int(value['volume'])
            audio_path = window['audio_path'].get()
            audio_original = dub.AudioSegment.from_file(audio_path) if os.path.exists(audio_path) else None

            # setting up timer
            hrs = int(value['hrs']); mins = int(value['mins']); secs = int(value['secs']); loop = value['loop']
            timer = hrs * 3600 + mins * 60 + secs
            paused = False
            goal = int(time()) + timer

            # writing new config
            new_config = {'hrs': f'{hrs:02d}', 'mins': f'{mins:02d}', 'secs': f'{secs:02d}', 'loop': loop,
                          'audio_path': audio_path, 'volume': volume}
            with open(f'{path}\\config', 'w') as file:
                file.write(str(new_config))

            # running timer
            while timer > 0:
                event, value = window.read(timeout=50)
                if window.was_closed():
                    break

                # update timer if not currently paused
                if not paused:
                    timer = goal - int(time())
                    window['timer'](value=f'{timer // 3600:02d}:{timer // 60 % 60:02d}:{timer % 60:02d}')

                if event == 'pause/resume':
                    if not paused:
                        paused = True
                        window['pause/resume'](text='Resume')
                    else:
                        paused = False
                        window['pause/resume'](text='Pause')
                        goal = int(time()) + timer

                # volume changes are effective next time the sound plays
                elif event == 'volume':
                    volume = int(value['volume'])
                    window['current_volume'](value=volume if volume < 0 else f'+{volume}')

                elif event == 'stop':
                    # reverting layout changes
                    window['hrs'](disabled=False)
                    window['mins'](disabled=False)
                    window['secs'](disabled=False)
                    window['loop'](disabled=False)
                    window['timer'](visible=False)
                    window['browse'](disabled=False)
                    window['stop'](visible=False)
                    window['pause/resume'](visible=False)
                    window['start'](visible=True)
                    break

                if timer <= 0:
                    # audio_original is None if sound file doesn't exist
                    if audio_original:
                        with (audio_original + volume).export(format='wav', tags={}, parameters=['-codec', 'copy']) as audio:
                            mixer.Sound(audio).play()

                    # reset timer if loop is checked
                    if loop:
                        timer = hrs * 3600 + mins * 60 + secs
                        goal = int(time()) + timer
                    else:
                        # when timer ends and not looping, accept only stop and close event
                        window['stop'](text='Return')
                        event = window.read()[0]
                        while event != 'stop':
                            if window.was_closed():
                                break
                            event = window.read()[0]
                        else:
                            # reverting layout changes
                            window['hrs'](disabled=False)
                            window['mins'](disabled=False)
                            window['secs'](disabled=False)
                            window['loop'](disabled=False)
                            window['browse'](disabled=False)
                            window['timer'](visible=False)
                            window['stop'](text='Stop', visible=False)
                            window['pause/resume'](visible=False)
                            window['start'](visible=True)
                            break

    mixer.quit()
    window.close()

main()

# Done_FIXME: FFmpeg uses a shitload of cpu (25%+) -> wasn't ffmpeg i just had to not do timeout=0 on windows.read(),
# who knew running a infinite loop with no rest cost so much, i definitely did Kappa
