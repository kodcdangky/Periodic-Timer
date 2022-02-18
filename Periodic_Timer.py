"""
Periodic Timer v1.0.0

A timer which plays a chosen sound when finished and when required, loops automatically and continuously

I made this to learn more about programming with GUIs and because I needed a timer like this for my own usage.

Feel free to download, modify, and use as you wish, as long as it's for non-commercial purposes

Made with:
- PySimpleGUI v4.56.0.13
- gensound v0.5.2
"""

import os
from time import time
from ast import literal_eval
import PySimpleGUI as sg
import gensound as gs
import gensound.io as gs_io

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
    # very nice theme for your eyes
    sg.theme('DarkGray11')

    # get the config of last run, or an empty dict if the file doesn't exist or is corrupted
    CONFIG = get_config(f'{path}\\config')

    # setting up gui elements and initializing
    sbx_hrs = sg.Spin(values=[f'{i:02d}' for i in range(10)], key='hrs', enable_events=True, size=2,
                      initial_value=CONFIG['hrs'] if 'hrs' in CONFIG else '00')
    TXT_HRS = sg.Text('hours')
    sbx_mins = sg.Spin(values=[f'{i:02d}' for i in range(60)], key='mins', enable_events=True, size=2,
                       initial_value=CONFIG['mins'] if 'mins' in CONFIG else '00')
    TXT_MINS = sg.Text('minutes')
    sbx_secs = sg.Spin(values=[f'{i:02d}' for i in range(60)], key='secs', enable_events=True, size=2,
                       initial_value=CONFIG['secs'] if 'secs' in CONFIG else '00')
    TXT_SECS = sg.Text('seconds')
    cbx_loop = sg.CBox('Loop', default=CONFIG['loop'] if 'loop' in CONFIG else True, key='loop', enable_events=True)

    sli_volume = sg.Slider(key='volume', range=(-30, 15), default_value=CONFIG['volume'] if 'volume' in CONFIG else 0,
                           resolution=1, orientation='h', disable_number_display=True, enable_events=True,
                           expand_x=True)
    txt_current_volume = sg.Text(
        text=int(sli_volume.DefaultValue) if sli_volume.DefaultValue < 0 else f'+{int(sli_volume.DefaultValue)}',
        size=3, key='current_volume')
    TXT_LABEL_VOLUME = sg.Text(text='Volume', key='label_volume')

    txt_timer = sg.Text('', key='timer', font='Arial 60 bold', text_color='#7de100', visible=False)

    btn_start = sg.Button('Start', key='start')
    btn_stop = sg.Button('Stop', key='stop', visible=False)
    btn_pause_resume = sg.Button('Pause', key='pause/resume', visible=False)

    btn_browse = sg.FileBrowse(button_text='Choose your alarm',
                               initial_folder=os.path.dirname(CONFIG['audio_path']) if 'audio_path' in CONFIG
                               else os.getenv('USERPROFILE'),
                               file_types=(('Audio Files', '*.mp3 *.wav *.ogg *.aac *.aif *.aifc *.aiff *.mp2 *.oga'),),
                               key='browse', target='audio_path')
    txt_audio_path = sg.Text(text=CONFIG['audio_path'] if 'audio_path' in CONFIG else '', expand_x=True,
                             key='audio_path')

    cbx_always_on_top = sg.CBox(text='Always on top', default=False, key='always_on_top', enable_events=True)

    LAYOUT = [
        [sg.Column([[sbx_hrs, TXT_HRS, sbx_mins, TXT_MINS, sbx_secs, TXT_SECS, cbx_loop], [TXT_LABEL_VOLUME, txt_current_volume, sli_volume], [sg.pin(txt_timer)]], element_justification='c'), sg.vbottom(sg.Column([[btn_start, btn_stop, btn_pause_resume]]))],
        [sg.pin(btn_browse), txt_audio_path, sg.Push(), cbx_always_on_top],
        ]
    window = sg.Window(title='Periodic Timer', layout=LAYOUT, finalize=True)
    # window = sg.Window(title='Periodic Timer', layout=LAYOUT, no_titlebar=True, keep_on_top=True,
    #                    right_click_menu=['', ['Exit']], right_click_menu_background_color='#fff',
    #                    right_click_menu_text_color='#000', right_click_menu_selected_colors=('#fff', '#313641'),
    #                    grab_anywhere=True, finalize=True)
    gs_io.IO.set_io('play', 'pygame')   # force gensound to use pygame
                                        # https://github.com/Quefumas/gensound/discussions/28#discussioncomment-2068837

    # window go brrr
    while not window.was_closed():
        event, value = window()

        # display updating
        if event not in (sg.WIN_CLOSED, 'Exit'):
            window['hrs'](value=f'{int(value["hrs"]):02d}')
            window['mins'](value=f'{int(value["mins"]):02d}')
            window['secs'](value=f'{int(value["secs"]):02d}')

        if event == 'always_on_top':
            if value['always_on_top']:
                window.keep_on_top_set()
            else:
                window.keep_on_top_clear()

        elif event == 'volume':
            window['current_volume'](value=int(value['volume']) if value['volume'] < 0 else f'+{int(value["volume"])}')

        elif event == 'start' and (int(value['hrs']) or int(value['mins']) or int(value['secs'])):
            # updating layout
            window['hrs'](disabled=True)
            window['mins'](disabled=True)
            window['secs'](disabled=True)
            window['loop'](disabled=True)
            window['browse'](visible=False)
            window['start'](visible=False)
            window['stop'](visible=True)
            window['pause/resume'](visible=True)
            window.refresh()  # refresh before showing timer so timer only shows once it starts running
            window['timer'](value=f'{value["hrs"]}:{value["mins"]}:{value["secs"]}', visible=True)

            # setting up audio
            volume = int(value['volume'])
            audio_path = window['audio_path'].get()
            audio_original = gs.WAV(audio_path) if os.path.exists(audio_path) else None

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
            while not window.was_closed() and timer > 0:
                event, value = window(timeout=15)

                # update timer if not currently paused
                if not paused:
                    timer = goal - int(time())
                    window['timer'](value=f'{timer // 3600:02d}:{timer // 60 % 60:02d}:{timer % 60:02d}')

                if event == 'always_on_top':
                    if value['always_on_top']:
                        window.keep_on_top_set()
                    else:
                        window.keep_on_top_clear()

                if event == 'pause/resume':
                    if not paused:
                        paused = True
                        window['pause/resume'](text='Resume')
                        window['timer'](text_color='#e17d00')  # orange while paused
                    else:
                        paused = False
                        window['pause/resume'](text='Pause')
                        window['timer'](text_color='#7de100')  # green while running
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
                    window['stop'](visible=False)
                    window['pause/resume'](visible=False)
                    window['start'](visible=True)
                    window['browse'](visible=True)
                    break

                if timer <= 0:
                    # audio_original is None if sound file doesn't exist
                    if audio_original:
                        (audio_original * gs.Gain(volume)).play()

                    # reset timer if loop is checked
                    if loop:
                        timer = hrs * 3600 + mins * 60 + secs
                        goal = int(time()) + timer
                    else:
                        # when timer ends and not looping, accept only stop and close event
                        window['stop'](text='Return')
                        window['timer'](text_color='#f00')  # red when finished
                        event, value = window()
                        while event != 'stop':
                            if window.was_closed():
                                break
                            elif event == 'always_on_top':
                                if value['always_on_top']:
                                    window.keep_on_top_set()
                                else:
                                    window.keep_on_top_clear()
                            event, value = window()
                        else:
                            # reverting layout changes
                            window['hrs'](disabled=False)
                            window['mins'](disabled=False)
                            window['secs'](disabled=False)
                            window['loop'](disabled=False)
                            window['timer'](visible=False, text_color='#7de100')
                            window['stop'](text='Stop', visible=False)
                            window['pause/resume'](visible=False)
                            window['start'](visible=True)
                            window['browse'](visible=True)
                            break

    window.close()

main()

# Done_FIXME: FFmpeg uses a shitload of cpu (25%+) -> wasn't ffmpeg i just had to not do timeout=0 on windows.read(),
# who knew running a infinite loop with no rest cost so much, i definitely did :)
