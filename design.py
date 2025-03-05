#8/6/2024 Elizabeth Li design.py
#take stimuli file: [list of image filenames]
#each trial: fix > masks > face > keypress options
#produce run file: [location, image, start_time, end_time, fix_color, timing]
    #start_time and end_time won't be used by main.py, they are just here for reference
#updated  code on 9/8/2024, but didn't run it to check if it actually works

import json
import random
import csv
import os
import numpy as np

N_RUNS = 4
N_LOC = 4 #4 possible locations for a face
FIX_DURATION = .7 #700 ms
MASK_DURATION = .15 #150 ms
FACE_DURATION = .15 #150 ms
BUTTON_DURATION = 10 #participants have up to 10 seconds to respond; variable response times will be take care of in main.py
N_FIX_COLOR = 32 #32 out of 224 fixation color change trials (14%)
BUFFER = 14 #14s for fixation cross event to wait for HRF, before experiment starts, and after experiment ends
    # chose 14s because estimate each trial = 3s, 8*3 = 24s

random.seed(29)



with open('image_filenames_8_19.csv', 'r') as file:                                                  #INPUT STIMULUS CSV NAME HERE
    reader = csv.reader(file)                               #the input csv should have each image filename on a row
    images = [row[0] for row in reader]                       #number of images = number of rows = number of trials


n_trials = len(images)
images_per_run = n_trials // N_RUNS #images per run is total trials/ number of runs

random.shuffle(images)

def balance_loc(n_trials, N_RUNS, N_LOC):
    face_locs = np.tile(np.arange(N_LOC), n_trials // N_LOC)
    np.random.shuffle(face_locs)

    runs_locs = []
    for run in range(N_RUNS):
        start_i = run * images_per_run
        end_i = start_i +images_per_run
        run_locs = face_locs[start_i:end_i]
        runs_locs.append(run_locs)

    return runs_locs

def buffer_fixation_event(trial_start_time):
    return{
        "location": None,
        "image": None,
        "start_time": trial_start_time,
        "end_time": trial_start_time + BUFFER,
        "fix_color": 'black',
        "timing": {
            "fix_duration": BUFFER,
            "mask_duration": None,
            "face_duration": None,
            "button_duration": None
        }}

def generate_trials(images, face_locs, fix_color_changes):
    trials = []
    trial_start_time = BUFFER #pre-experiment buffer

    #generate trial details
    for trial in range(n_trials):
        #insert 14s fixation cross every 8 trials, excluding after the last trial
        if (trial + 1) % 8 == 0 and trial != n_trials - 1:
            trials.append(buffer_fixation_event(trial_start_time))
            #increment start time for next trial
            trial_start_time += BUFFER


        fix_color = 'blue' if trial in fix_color_changes else 'black'
        location = face_locs[trial]

        #meat of the experiment
        trial_details = {
            "location": location, #location of a face image
            "image": images[trial], #image filename
            "start_time": trial_start_time,
            "end_time": trial_start_time + FIX_DURATION + MASK_DURATION + FACE_DURATION + BUTTON_DURATION,
            "fix_color": fix_color,
            "timing":{
                "fix_duration": FIX_DURATION,
                "mask_duration": MASK_DURATION,
                "face_duration": FACE_DURATION,
                "button_duration": BUTTON_DURATION
            }}
        trials.append(trial_details)

        # increment start time for next trial
        trial_start_time += FIX_DURATION + MASK_DURATION + FACE_DURATION + BUTTON_DURATION


    #post-experiment buffer
    trials.append(buffer_fixation_event(trial_start_time))

    return trials


def write_run_file(trials, run_number):
    #create runs directory if it doesn't exist
    if not os.path.exists('runs'):
        os.makedirs('runs')

    with open(f'runs/run{run_number}.json', 'w') as file:
        json.dump(trials, file)


face_locs_by_run = balance_loc(n_trials, N_RUNS, N_LOC)


for run in range(1, N_RUNS+1):
    start_index = (run-1) * images_per_run
    end_index = start_index + images_per_run
    run_images = images[start_index:end_index]

    # randomly select color change trials for each run
    fix_color_changes = random.sample(range(images_per_run), N_FIX_COLOR // N_RUNS)

    write_run_file(generate_trials(run_images, face_locs_by_run[run-1]), run)
    #the main function: takes images, face locations, and run number; writes the run file