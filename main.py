#8/7/2024 Elizabeth Li main.py
# loads run files [location, image, start_time, end_time, fix_color]
# displays stimuli with specified timing
# produces log files {'stim_events': [], 'key_events':[], 'subject': _, 'run': _}
    #within stim_events: {'stimulus_type': [], 'start_time': [], 'end_time': [], 'color': [], 'image': [], 'location': []}
# mask should be named mask.png

from psychopy import visual, core, event, logging
import json
import os
from glob import glob
from datetime import datetime

N_RUNS = 4
N_LOC = 4 #4 possible locations for a face
# FIX_DURATION = .7 #700 ms
# MASK_DURATION = .15 #150 ms
# FACE_DURATION = .15 #150 ms
# BUTTON_DURATION = 10 #participants have up to 10 seconds to respond; variable response times will be take care of in main.py
# N_FIX_COLOR = 32 #32 out of 224 fixation color change trials (14%)

if __name__ == '__main__':
    sid = input("Subject ID: ")

    #determine the next run number based on existing logs
    logs = glob(f'logs/{sid}_run*.json')
        #find all finishes files for the project
        #if there are no finished files, logs will be an empty list
    runs = [int(log.split('_')[1][3:]) for log in logs] #extract run number from filename
        #ex. for the filename "logs/SID001234_run1_20230730-123456.json":
        #split based on the delimiter "_", get ['logs/SID001234', 'run1', '20230730-123456']
        #choose second element 'run1, its fourth character '1'
    run = 1 if not runs else max(runs)+1 #determine the next run number
        #if the 'runs' list is empty, run = 1
        #otherwise, add 1 to the existing run number
    assert run in range(1, N_RUNS+1) #ensure that the run number is 1, 2, 3, or 4

    #load run file
    try:
        with open(f'runs/{run}.json', 'r') as file:
            trials = json.load(file)
    except FileNotFoundError:
        print(f"Run file for run {run} not found.")
        exit()

    #define file names
    timelabel = datetime.now().strftime('%Y%m%d-%H%M%S')
    os.makedirs('logs', exist_ok=True)
    start_fn = f'logs/{sid}_run{run}_{timelabel}_start.json'
    finish_fn = f'logs/{sid}_run{run}_{timelabel}.json'

    # set up quit key (ctrl + Q)
    event.globalKeys.clear()
    event.globalKeys.add(key='q', modifiers=['ctrl'], func=core.quit)

    # set up psychopy window
    win = visual.Window(size=[1920,1080], allowGUI=False, units='pix',screen=0, color='#D3D3D3', fullscr=True)
    # allowGUI=False means to disable graphic UI decorations, such as borders or control buttons
    # screen=0 means that the window should be created on the primary monitor, usually the main display

    #create stimuli
    black_fix = visual.TextStim(win, text='+',height=80, pos=(0,0), color='black')
    blue_fix = visual.TextStim(win, text='+',height=80, pos=(0,0), color='blue')
    masks = [visual.ImageStim(win, image='mask.png', pos = (i*200-300,0)) for i in range(N_LOC)]
        #x-coord of masks are currently at -300, -100, 100, 300
        #adjust positions accordingly
    # create an ImageStim object which will be the face image, addition details are added later
    face_stim = visual.ImageStim(win)

    #initialize results dictionary
    data_log = {'stim_events': [], 'key_events': [], 'subject': sid, 'run': run}
    stim_events = []
    key_events = []

    #synchronize the exp with the scanner
    print('Waiting for trigger')
    event.waitKeys(keyList=['5'])  # Wait for scanner to send '5' key
    print('Starting experiment')

    #initalize clock
    clock = core.Clock()
    exp_start_time = datetime.now()
    data_log['exp_start_time'] = exp_start_time.strftime('%Y%m%d-%H%M%S')

    #save initial state in case scan terminates early
    with open(start_fn, 'w') as f:
        json.dump(data_log,f)


    for trial in trials:
        #set fixation cross color
        fix = blue_fix if trial['fix_color'] == 'blue' else black_fix

        #display fixation cross
        fix.draw()
        win.flip()
        fix_start_time = clock.getTime()
        core.wait(trial['timing']['fix_duration']) #show fixation cross for FIX_DURATION seconds, as specified in design.py
        fix_end_time = clock.getTime()
        #append the fixation event
        stim_events.append({'stimulus_type': 'fixation', 'start_time': fix_start_time, 'end_time': fix_end_time, 'color': trial['fix_color'], 'image': None, 'location': None})

        #display masks (w fixation cross)
        fix.draw()
        for mask in masks:
            mask.draw()
        win.flip()
        mask_start_time = clock.getTime()
        core.wait(trial['timing']['mask_duration']) #show fixation cross for MASK_DURATION seconds, as specified in design.py
        mask_end_time = clock.getTime()
        stim_events.append({'stimulus_type': 'mask', 'start_time': mask_start_time, 'end_time': mask_end_time, 'color': trial['fix_color'], 'image': None, 'location': None})

        #display face (w fixation cross)
        fix.draw()
        face_stim.image = trial['image']
        face_stim.pos = (trial['location']*200-300, 0) #adjust locations
        face_stim.draw()
        win.flip()
        face_start_time = clock.getTime()
        core.wait(trial['timing']['face_duration']) #show fixation cross for FACE_DURATION seconds, as specified in design.py
        face_end_time  = clock.getTime()
        stim_events.append({'stimulus_type': 'face', 'start_time': face_start_time, 'end_time': face_end_time, 'color': trial['fix_color'], 'image': trial['image'], 'location': trial['location']})

        #get response
        clock.reset()
        response = event.waitKeys(maxWait = trial['timing']['button_duration'], keyList=['1', '2', '3'], timeStamped=clock)
        #waitKeys pauses the script to key for a keypress

        #record trial data
        if response:
            key_events.append({'key': response[0][0], 'time': response[0][1]})
            #response is a list of tuples; but in this case there's only a single keypress, so one tuple
            #response[0][0] is first element from the first tuple
            #response[0][1] is second element from the first tuple
        else:
            key_events.append({'key': None, 'time': None})

        win.flip() #clear screen

    #record experiment end time
    exp_end_time = datetime.now()
    data_log['exp_end_time'] = exp_end_time.strftime('%Y%m%d-%H%M%S')
    print(exp_start_time, exp_end_time)

    if not os.path.exists('logs'):
        os.makedirs('logs')

    #save results to log file
    with open(finish_fn, 'w') as f:
        json.dump(data_log, f)

    win.close() #close window
    core.quit() #quit PsychoPy










