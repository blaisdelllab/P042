#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 16:41:47 2026

@author: marisacalarco & kayleyozimac

Last updated 2026-7-13

This is the code for the 'Extinction of Conditioned Inhibition' project (P042) 
ITERATION 3 (P042a.iii)

This is an adjacent replication of P021, an off shoot of the 'Suboptimal Choice Task' study


Training Phase: We will begin with excitation training of stimuli A, B, and C along with
inhibition training of AX, and exposure to Y (4 trials the first session) 
    Trials begin with an 10-15s variable ITI
    There is then a 30s pre-stimulus phase
    Stimulus A, B, C, AX, or Y is then presented for 30s 
        Stimulus order is randomized, with constraints on repetition of the same stimulus
    A, B, and C trials are followed by food reward (5s)
    AX and Y trials are never followed by food reward
    Return to ITI after reward or lack of reward 


Extinction Phase: We will divide subjects into three equal sized groups, which will 
undergo unique extinction procedures,  
    Group Extinction A: Extcinction training of A, B+ and C+ presentattions  (A-/B+/C+)
    Group Extinction X: Extinction training of X, B+ and C+ presentations  (X-/B+/C+)
    Group Extinction C: Extinction training of C, A+ and B+ presentations  (A+/B+/C-)
    Trials follow the same structure as training 
        10-15s ITI, 30s pre-stimulus stage, 30s stimulus stage, 
        5s reward and then ITI or straight to ITI
    
    
Testing Phase: We will test stimuli BX and BY interspersed with B+ presentations
B and BX serve as a summation test, while BY serves as a control for external inhibition
    Trials follow the same structure as training 


Recovery Phase: After 3 weeks, we will test stimulus A, AX, BX, and BY to evaluate if 
spontaneous recovery has occured with regards to excitor A for the Extinction A group. 
Again B+ trials will be interspersed. If recovery is not observed, we will re-excite A+ 
in a second training phase and carry out this second testing phase again.

"""

# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
# =============================================================================
from csv import writer, QUOTE_MINIMAL, DictReader
from datetime import datetime, timedelta, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from time import time, sleep
from os import getcwd, popen, mkdir, listdir, path as os_path
from random import choice, shuffle
from PIL import ImageTk, Image  

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis.

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        # Import additional libraries...
        import pigpio # import pi, OUTPUT
        import csv
        #...including art scripts
        sys_path.insert(0, str(os_path.expanduser('~')+"/Desktop/Experiments/P033/"))
        import graph
        import polygon_fill
        
        # Setup GPIO numbers (NOT PINS; gpio only compatible with GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21
        
        # Setup use of pi()
        rpi_board = pigpio.pi()
        
        # Then set each pin to output 
        rpi_board.set_mode(servo_GPIO_num,
                           pigpio.OUTPUT) # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num,
                           pigpio.OUTPUT) # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num,
                           pigpio.OUTPUT) # House light LED...
        
        # Setup the servo motor 
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    50) # Default frequency is 50 MhZ
        
        # Next grab the up/down 
        hopper_vals_csv_path = str(os_path.expanduser('~')+"/Desktop/Box_Info/Hopper_vals.csv")
        
        # Store the proper UP/DOWN values for the hopper from csv file
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]
        
        # Lastly, run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
                             
        
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

# Below  is just a safety measure to prevent too many recursive loops). It
# doesn't need to be changed.
setrecursionlimit(5000) 

"""

The code below jumpstarts the loop by first building the hopper object and 
making sure everything is turned off, then passes that object to the
control_panel. The program is largely recursive and self-contained within each
object, and a macro-level overview is:
    
    ControlPanel -----------> MainScreen ------------> PaintProgram
         |                        |                         |
    Collects main           Runs the actual         Gets passed subject
    variables, passes      experiment, saves        name, but operates
    to Mainscreen          data when exited          independently
    

"""

# The first of two objects we declare is the ExperimentalControlPanel (CP). It
# exists "behind the scenes" throughout the entire session, and if it is exited,
# the session will terminate.
class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # First, setup the data directory in "Documents"
        self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
        # Next up, we need to do a couple things that will be different based
        # on whether the program is being run in the operant boxes or on a 
        # personal computer. These include setting up the hopper object so it 
        # can be referenced in the future, or the location where data files
        # should be stored.
        if operant_box_version:
            # Setup the data directory in "Documents"
            self.data_folder = "P042_data" # The folder within Documents where subject data is kept
            self.data_folder_directory = str(os_path.expanduser('~'))+"/Desktop/Data/" + self.data_folder
        else: # If not, just save in the current directory the program us being run in 
            self.data_folder_directory = getcwd() + "/data"
        
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P042a.iii Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Thoth", "Joplin", "Odin", "Mario", "Luigi", "Itzamna", "Durrell", "Vonnegut", "Wenchang"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Subject")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()

        
        # Exp phases
        self.experimental_phase_titles = ["Phase 1 (Training)", 
                                          "Phase 2 (First Test)",
                                          "Phase 3 (Extinction)",
                                          "Phase 4 (Second Test)",
                                          "Phase 5 (Recovery)"]
        
        Label(self.control_window, text="Experimental Phase:").pack()
        self.exp_phase_variable = StringVar(self.control_window)
        self.exp_phase_variable.set("Select")
        self.exp_phase_menu = OptionMenu(self.control_window,
                                          self.exp_phase_variable,
                                          *self.experimental_phase_titles
                                          ).pack()
        
        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
        
    def set_pigeon_ID(self, pigeon_name):
        try:
            if not os_path.isdir(self.data_folder_directory):
                mkdir(self.data_folder_directory)
    
            subject_dir = os_path.join(self.data_folder_directory, pigeon_name)
            if not os_path.isdir(subject_dir):
                mkdir(subject_dir)
                print(f"\n ** NEW DATA FOLDER FOR {pigeon_name.upper()} CREATED **")
            else:
                print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")
        except Exception as e:
            print("Error creating data folder:", e)
                
                
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            if self.exp_phase_variable.get() != "Select":
                print("Operant Box Screen Built") 
                self.MS = MainScreen(
                    str(self.subject_ID_variable.get()), # subject_ID
                    self.record_data_variable.get(), # Boolean for recording data (or not)
                    self.data_folder_directory, # directory for data folder
                    self.exp_phase_variable.get(), # Exp phase name
                    self.experimental_phase_titles.index(self.exp_phase_variable.get()) # Exp Phase number (0-1)
                    )
            else:
                print("\n ERROR: Input Stimulus Set Before Starting Session")
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")

#This is where we set up our experiment
            
class MainScreen(object):
    # First, we declare several functions that are called within the initial
    # __init__() function that is run when the object is first built
    
    def __init__(self, subject_ID, record_data, data_folder_directory,
                 exp_phase_name, exp_phase_num):
        # Here, we set up all the variables passed from within the control
        # panel object to this MainScreen object
        # We set up each argument as "self." objects to make them global 
        # within this object 
        
        self.exp_phase_name = exp_phase_name
        self.exp_phase_num = exp_phase_num
        if self.exp_phase_num == 0:
            self.exp_phase_name = "Phase 1 (Training)"
        if self.exp_phase_num == 1:
            self.exp_phase_name = "Phase 2 (First Test)"
        if self.exp_phase_num == 2:
            self.exp_phase_name = "Phase 3 (Extinction)"
        if self.exp_phase_num == 3:
            self.exp_phase_name = "Phase 4 (Second Test)"
        if self.exp_phase_num == 3:
            self.exp_phase_name = "Phase 5 (Recovery)"
            
        self.data_folder_directory = data_folder_directory
    
        self.subject_ID = subject_ID
        self.record_data = record_data
        
        self.root = Toplevel()
        self.root.title(f"P042 {self.exp_phase_name}: ")
        self.mainscreen_height = 768
        self.mainscreen_width = 1024
        self.root.bind("<Escape>", self.exit_program)
        
        # If the version is the one running in the boxes...
        if operant_box_version: 
            # Keybind relevant keys
            self.cursor_visible = True # Cursor starts on...
            self.change_cursor_state() # turn off cursor UNCOMMENT
            self.root.bind("<c>",
                           lambda event: self.change_cursor_state()) # bind cursor on/off state to "c" key
            # Then fullscreen (on a 1024x768p screen). Assumes that both screens
            # that are being used have identical dimensions
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  1024x768p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()
            
        self.start_time = datetime.now()
        self.trial_start = None
        self.stimulus_start_time = None
        if not operant_box_version or self.subject_ID == "TEST":
            self.ITI_duration = choice([3000, 4000, 5000])   # 3–5 sec
            self.pre_CS_duration = 5000
        else: 
            self.ITI_duration = choice([
                10000, 11000, 12000, 13000, 14000,
                15000, 16000, 17000, 18000, 19000, 20000])  # 10–20 sec
            self.pre_CS_duration = 30000
        if not operant_box_version or self.subject_ID == "TEST":
            self.hopper_duration = 3000
# CHANGE LUIGI HOPPER TO 4s here
        elif self.subject_ID == "Luigi":
            self.hopper_duration = 4000
        else:
            self.hopper_duration = 5000
        
        self.reinforced_trial_counter = 0
        self.last_written_trial_num = None
        if self.exp_phase_num == 0:
            self.max_number_of_trials = 60 # 64 if Y on
        elif self.exp_phase_num == 2:
            self.max_number_of_trials = 20 # 20 trials for testing
        elif self.exp_phase_num == 3:
            self.max_number_of_trials = 28 # 28 trials for spontaneous recovery testing
        else:
            self.max_number_of_trials = 60
            
        self.session_data_frame = []
        self.trial_stage = 0
        self.current_trial_counter = 0
        self.trial_type = []
        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord",	"Ycord", "Event",	
            "TrialTime", "TrialStage", "TrialType",	"SignTrackingPecks", "BackgroundPeckNum",
            "TotalPeckCount", "PreStimulusPecks", "TrialNum", "ReinforcedTrialNum", "Date"] 
        self.session_data_frame.append(header_list)
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL'
        
        # -----------------------------------------------------------------------
        # LOAD STIMULI
        # Load stimulus images from a folder
        # on the desktop. Each image will be displayed twice in the diamond grid.
        # -----------------------------------------------------------------------
        if operant_box_version:
            self.stimuli_path = "/home/blaisdelllab/Desktop/Experiments/P042/P042_stimuli"
        else:
            self.stimuli_path = "/Users/marisacalarco/Desktop/lab/P042_stimuli"

        # -----------------------------------------------------------------------
        # DIAMOND IMAGE LAYOUT
        #
        # Each stimulus image is rotated 45 degrees so it appears as a diamond.
        # Two copies are placed touching at their points (tight spacing like the
        # original script), centered on screen.
        #
        #          [top]         (cx,        cy - OFFSET)
        #   [left]       [right] (cx-OFFSET, cy) / (cx+OFFSET, cy)
        #          [bot]         (cx,        cy + OFFSET)
        #
        # Excitors (A, B, C) -> top + bottom  (vertical axis)
        # Inhibitors (X, Y)  -> left + right  (horizontal axis)
        #
        # CELL_SIZE: side of the square image before rotation.
        # After 45 degree rotation the image spans CELL_SIZE*sqrt(2) tip-to-tip.
        # DIAMOND_OFFSET = half that span, so the two diamonds kiss at their tips.
        # -----------------------------------------------------------------------
        import math

        self.CELL_SIZE = 80   # square px before rotation; tweak to resize

        # Half the tip-to-tip diagonal of the rotated square
        self.DIAMOND_OFFSET = int((self.CELL_SIZE / 2) * math.sqrt(2)) - 4

        cx = self.mainscreen_width  // 2
        cy = self.mainscreen_height // 2

        self.DIAMOND_CENTERS = {
            "top":    (cx,                       cy - self.DIAMOND_OFFSET),
            "bottom": (cx,                       cy + self.DIAMOND_OFFSET),
            "left":   (cx - self.DIAMOND_OFFSET, cy),
            "right":  (cx + self.DIAMOND_OFFSET, cy),
        }

        self.POSITIONS = {
            "A": ["top", "bottom"],
            "B": ["top", "bottom"],
            "C": ["top", "bottom"],
            "X": ["left", "right"],
            "Y": ["left", "right"],
        }

        # Load, resize, rotate 45 degrees, and store each image.
        # If ANY image file is missing the session will not start.
        
        # Counterbalance X and Y stimuli 
        if self.subject_ID in ["Luigi", "Itzamna", "Joplin", "Wenchang", "TEST"]:
            file_map = {
                        "A": "A_iii.bmp",
                        "B": "B_iii.bmp",
                        "C": "C_iii.bmp",
                        "X": "X_iii.bmp",
                        "Y": "Y_iii.bmp"
                    }
        elif self.subject_ID in ["Mario", "Odin", "Thoth", "Vonnegut", "Durrell"]:
            file_map = {
                        "A": "A_iii.bmp",
                        "B": "B_iii.bmp",
                        "C": "C_iii.bmp",
                        "X": "X2_iii.bmp",
                        "Y": "Y2_iii.bmp"
                    }
            
        self.stimulus_images = {}
        missing = []
        for stim_key, filename in file_map.items():
            img_path = os_path.join(self.stimuli_path, filename)
            if not os_path.isfile(img_path):
                missing.append(img_path)
            else:
                img = Image.open(img_path).convert("RGBA").resize(
                    (self.CELL_SIZE, self.CELL_SIZE), Image.LANCZOS
                )
                img_rot = img.rotate(45, expand=True, resample=Image.BICUBIC)
                self.stimulus_images[stim_key] = ImageTk.PhotoImage(img_rot)
                print(f"Loaded & rotated stimulus image: {img_path}")
                

        if missing:
            self.root.destroy()
            raise FileNotFoundError(
                "\n\nERROR: The following stimulus image(s) were not found:\n"
                + "\n".join(f"  {p}" for p in missing)
                + f"\n\nExpected folder: {self.stimuli_path}"
                + "\nSession aborted. Please add the missing files and restart."
            ) 
        
        self.place_birds_in_box()
        
    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        self.root.bind("<space>", self.first_ITI) # bind cursor state to "space" key
        #shows program text (i.e., what was chosen in the control panel)
        self.mastercanvas.create_text(512,384,
                                      fill="white",
                                      font="Times 26 italic bold",
                                      text=f"P042a.iii \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase: {self.exp_phase_name}")

    def first_ITI(self, event):
        print("Spacebar pressed -- SESSION STARTED") 
        
        self.trial_stage = 0 #First substage
    
        # Trial assignment for training
        
        if self.exp_phase_num == 0: #Training Phase
            
           # Core training cues per spec: A+/B+/C+, AX-
            
           # Training trial proportions:
           # 60 total trials (10 blocks of 5)
           # Each block: 2 AX-, 1 A+, 1 B+, 1 C+ (randomized order per block)
           
            self.trial_types = ["A", "B", "C", "AX"]
           
           # Define block composition and total trials
            trial_blocks = ["AX", "AX", "A", "B", "C"]
            n_blocks = 12  # 12 blocks × 5 trials = 60 total
           
            self.trial_assignment_list = []
           
            for _ in range(n_blocks):
               block = trial_blocks[:]  
               shuffle(block)        # randomize order within block
               self.trial_assignment_list.extend(block)
            

        # Optional: add 4 Y exposures in first session (leave False all other days)
            include_Y_this_session = True
            if include_Y_this_session:
                # Insert 4 Y-trials, one in each 15-trial block
                import random
                
                # Block boundaries: 0–15, 16-30, 31-45, 46-60
                block_ranges = [
                    (0, 15),
                    (16, 30),
                    (31, 45),
                    (46, 60),
                ]
                
                # Pick random insertion indexes
                Y_positions = [random.randint(start, end) for start, end in block_ranges]
                
                # Sort so insertion doesn't shift later indices
                Y_positions.sort()
                
                # Insert "Y" trials into the list
                for pos in Y_positions:
                    self.trial_assignment_list.insert(pos, "Y")
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Training trial list ({self.max_trials}): {self.trial_assignment_list}")
        
        elif self.exp_phase_num == 1: # First Testing Phase 
            
           # Testing trial proportions:
               # 20 total trials (4 blocks of 5)
               # Each block: 3 B+, 1 BX-, 1 BY- (randomized order per block)
               # First block: start with all three B+ 

            self.trial_types = ["B", "BX", "BY"]
            
            self.trial_assignment_list = []
           
            # First block
        
            # Counterbalance cue (BX or BY) birds see first by ext. group
            # BX first
            if self.subject_ID in ["Joplin", "Odin", "Luigi", "Wenchang", "TEST"]: 
                first_block = ["B", "B", "B", "BX", "BY"]
            
            # BY first
            elif self.subject_ID in ["Itzamna", "Mario", "Thoth", "Vonnegut", "Durrell"]: 
                first_block = ["B", "B", "B", "BY", "BX"]
               
            self.trial_assignment_list.extend(first_block)

            # Create rest of trial blocks
            # Define block composition and total trials
            trial_blocks = ["B", "B", "B", "BX", "BY"]
            n_blocks = 3  # 4 blocks total × 5 trials = 20 total

            for _ in range(n_blocks):
                block = trial_blocks[:]  
                shuffle(block)        # randomize order within block
                self.trial_assignment_list.extend(block)
            
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Testing trial list ({self.max_trials}): {self.trial_assignment_list}")  
            

        elif self.exp_phase_num == 2: # Extinction Phase
        
        #group assignments 
        
        # iteration 1: 
            # Extinction A = Joplin Itzamna Vonnegut
            # Extinction X = Luigi Thoth Durrell
            # Extinction C = Odin Mario Wenchang
            
        # iteration 2: 
            # Extinction A = Thoth Odin Durrell
            # Extinction X = Joplin Mario Wenchang
            # Extinction C = Itzamna Luigi Vonnegut
            
        # iteration 3: 
            # Extinction A = Luigi Mario Wenchang
            # Extinction X = Itzamna Odin Vonnegut
            # Extinction C = Joplin Thoth Durrell
        
        # Build trial lists for Extinction A, Extinction C          
            if self.subject_ID in ["Luigi", "Mario", "Wenchang", "Joplin", "Thoth", "Durrell", "TEST"]: 
                self.trial_types = ["A", "B", "C"]
        # Build trial list for Group Extinction X
            elif self.subject_ID in ["Itzamna", "Odin", "Vonnegut"]: 
                self.trial_types = ["X", "B", "C"]
          
            desired_total = self.max_number_of_trials
            block_template = self.trial_types[:]               # one of each
            block_size = len(block_template)                   # 3
            n_full_blocks = desired_total // block_size
            tail = desired_total % block_size
    
            # Build shuffled full blocks
            self.trial_assignment_list = []
            for _ in range(n_full_blocks):
                blk = block_template[:]
                shuffle(blk)
                self.trial_assignment_list.extend(blk)
    
            # Add a (shuffled) partial block if needed (no repeats within tail)
            if tail > 0:
                tail_blk = block_template[:]
                shuffle(tail_blk)
                self.trial_assignment_list.extend(tail_blk[:tail])
           
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Extinction trial list ({self.max_trials}): {self.trial_assignment_list}")
            
        
        elif self.exp_phase_num == 3: # Second Testing Phase 
            
           # Testing trial proportions:
               # 20 total trials (4 blocks of 5)
               # Each block: 3 B+, 1 BX-, 1 BY- (randomized order per block)
               # First block: start with all three B+ 

            self.trial_types = ["B", "BX", "BY"]
            
            self.trial_assignment_list = []
           
            # First block
        
            # Counterbalance cue (BX or BY) birds see first by ext. group
            # BX first
            if self.subject_ID in ["Joplin", "Odin", "Luigi", "Wenchang", "TEST"]: 
                first_block = ["B", "B", "B", "BX", "BY"]
            
            # BY first
            elif self.subject_ID in ["Itzamna", "Mario", "Thoth", "Vonnegut", "Durrell"]: 
                first_block = ["B", "B", "B", "BY", "BX"]
               
            self.trial_assignment_list.extend(first_block)

            # Create rest of trial blocks
            # Define block composition and total trials
            trial_blocks = ["B", "B", "B", "BX", "BY"]
            n_blocks = 3  # 4 blocks total × 5 trials = 20 total

            for _ in range(n_blocks):
                block = trial_blocks[:]  
                shuffle(block)        # randomize order within block
                self.trial_assignment_list.extend(block)
            
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Testing trial list ({self.max_trials}): {self.trial_assignment_list}")  
            
        elif self.exp_phase_num == 4: # Recovery Phase
            
           # Testing trial proportions:
               # 28 total trials (4 blocks of 7)
               # Each block: 1 A-, 1 AX-, 3 B+, 1 BX-, 1 BY- (randomized order per block)
               # First block: start with all three B+ 

            self.trial_types = ["A", "AX", "B", "BX", "BY"] 
            
            self.trial_assignment_list = []

            # First block
            
            # Show B+ trials first
            if self.subject_ID in ["Joplin", "Odin", "Luigi", "Wenchang", "TEST"]: 
                first_block = ["B", "B", "B", "BX", "BY", "A", "AX"]
            
            # BY first
            elif self.subject_ID in ["Itzamna", "Mario", "Thoth", "Vonnegut", "Durrell"]: 
                first_block = ["B", "B", "B", "BY", "BX", "A", "AX"]
                
            self.trial_assignment_list.extend(first_block)

            # Create rest of trial blocks
            # Define block composition and total trials
            trial_blocks = ["B", "B", "B", "A", "AX", "BX", "BY"]
            n_blocks = 3  # 4 blocks total × 7 trials = 28 total

            for _ in range(n_blocks):
                block = trial_blocks[:]  
                shuffle(block)        # randomize order within block
                self.trial_assignment_list.extend(block)
            
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Recovery trial list ({self.max_trials}): {self.trial_assignment_list}") 
        
    
        # Session timing constants
        self.stimulus_ms = 30000
        # Excitor vs. inhibitor reinfrocement mappings
        self.reinforce_map = {"A": True, "B": True, "C": True, "AX": False, "Y": False}
    
        #Housekeeping
        
        self.current_trial_counter = 0 
        self.root.unbind("<space>") # bind cursor state to "space" key
        self.clear_canvas()
        self.start_time = datetime.now()  # This is the ACTUAL time the session starts
        self.target_peck_counter = 0
        self.background_peck_counter = 0
        self.total_peck_counter = 0  
        self.pre_CS_peck_counter = 0
        
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(0, 0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill="black",
                                           outline="black",
                                           tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, event_type="ITI_peck": self.write_data(event, 
                                                                                        event_type))
        
        if not operant_box_version or self.subject_ID == "TEST": # If test, don't worry about first ITI delay
            self.ITI_duration = 1 * 3000
            self.root.after(1, lambda: self.ITI(None))
        else:
            self.ITI_duration = 1 * 30000
            self.root.after(30000, lambda: self.ITI(None))
            
            
            
    
    def ITI(self, event):
        self.clear_canvas()
        
        self.trial_stage = 0
        self.stimulus_start_time = None
        
        # First check:
        if self.current_trial_counter >= self.max_trials:
            self.exit_program("event")
            return
        
        # Only access and increment AFTER confirming you're within bounds
        self.trial_type = self.trial_assignment_list[self.current_trial_counter]
        self.current_trial_counter += 1


        # Draw black background that logs ITI pecks
        self.mastercanvas.create_rectangle(0, 0, #coordinates
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill="black",
                                           outline="black",
                                           tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, event_type="ITI_peck": self.write_data(event, event_type))
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num,
                    False) # Turn off the hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                   hopper_down_val) # Hopper down
            rpi_board.write(house_light_GPIO_num, 
                    False) # Turn off house light
        
        # Optional onscreen ITI text for test mode
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(512, 374,
                                          fill="white",
                                          font="Times 25 italic bold",
                                          text=f"ITI ({int(self.ITI_duration / 1000)} sec.)")

        # Reset per-trial variables
        self.trial_start = datetime.now()
        self.target_peck_counter = 0
        self.background_peck_counter = 0
        self.total_peck_counter = 0  
        self.pre_CS_peck_counter = 0
        
        # Write last trial’s data
        # self.write_comp_data(False)
        
        # Reset ITI duration after the first trial
        # Randomize ITI duration each trial using choice()
        if not operant_box_version or self.subject_ID == "TEST":
            self.ITI_duration = choice([3000, 4000, 5000])   # 3–5 sec
        else:
            self.ITI_duration = choice([
                10000, 11000, 12000, 13000, 14000,
                15000, 16000, 17000, 18000, 19000, 20000
            ])  # 10–20 sec

        # Print headers and trial-type info
        print(f"\n{'*' * 30} Trial {self.current_trial_counter} begins {'*' * 30}")
        print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")
        
        self.root.after(self.ITI_duration, self.pre_CS_phase)




    def pre_CS_phase(self, event=None):
        
        """Present blank screen before stimulus for self.pre_CS_ms, log pecks."""
        
        self.clear_canvas()
        self.write_data(None, "pre_trial_started")

        self.trial_stage = 1 
        self.trial_start = datetime.now()
        self.stimulus_start_time = datetime.now()

        # Full-screen background(logs background_peck)
        self.mastercanvas.create_rectangle(0, 0, 
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill="black", 
                                           outline="black", 
                                           tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, event_type="pre_CS_peck": self.write_data(event, event_type))
        
        # Optional onscreen ITI text for test mode
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(512, 374,
                                          fill="white",
                                          font="Times 25 italic bold",
                                          text=f"pre-CS ({int(self.pre_CS_duration / 1000)} sec.)")
        
        # Reset ITI duration after the first trial
        if not operant_box_version or self.subject_ID == "TEST":
            self.pre_CS_duration = 5000
        else:
            self.pre_CS_duration = 30000
        
        self.root.after(self.pre_CS_duration, self.stimulus_phase)
    
    
    
    
    def stimulus_phase(self, event=None):
        
        """Present the current trial's stimulus for self.stimulus_ms, log pecks."""
        
        self.clear_canvas()
        self.write_data(None, "trial_started")
        # Peck counts from pre-CS phase reset
    
        # Full-screen background (logs background_peck)
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, 
            self.mainscreen_height,
            fill="black",
            outline="black", 
            tag="bkgrd"
        )

        # Receptive field: diamond (square rotated 45 degrees) centred on screen.
        # receptivefield_size is the tip-to-tip span of the diamond.
        receptivefield_size = 297
        x_center = self.mainscreen_width / 2
        y_center = self.mainscreen_height / 2
        half = receptivefield_size / 2
 
        self.mastercanvas.create_polygon(
            x_center,        y_center - half,   # top tip
            x_center + half, y_center,           # right tip
            x_center,        y_center + half,    # bottom tip
            x_center - half, y_center,           # left tip
            fill="black",
            outline="black",
            tag="receptivefield"
        )
        
        self.mastercanvas.tag_bind(
            "bkgrd", 
            "<Button-1>",
            lambda e, 
            event_type="background_peck": self.write_data(e, event_type)
        )
    
        # Draw the actual cue (A/B/C single; AX overlays A then X)
        
        self._draw_stimulus_rects(self.trial_type)

        # Bind stimulus clicks to target_peck (affects both black region + colored squares)
       
        self.mastercanvas.tag_bind(
             "stimulus", "<Button-1>",
            lambda e, event_type="target_peck": self.write_data(e, event_type)
        )
    
        # House light on while stimulus is present (box only)
        if operant_box_version:
            try:
                rpi_board.write(house_light_GPIO_num, True)
            except Exception:
                pass
    
        # Mark stimulus start time and schedule stimulus offset
        self.trial_stage = 2  # stimulus on
        #self.trial_start = datetime.now()
        #self.stimulus_start_time = datetime.now()
    
        # Optional label for TEST runs
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(
                512, 60, fill="white", font="Times 26",
                text=f"Trial {self.current_trial_counter}/{self.max_trials} • {self.trial_type}"
            )
            
        if not operant_box_version or self.subject_ID == "TEST":
            self.stimulus_ms = 5000 
        else:
            self.stimulus_ms = 30000
        
        # End of stimulus after self.stimulus_ms
       
        # Training: 
        # If excitor, send to reinforcement; if inhibitor, send to ITI
        if self.exp_phase_num == 0: #Training Phase
            if self.trial_type in ("A", "B", "C"):
                self.root.after(self.stimulus_ms, self.reinforcement_phase)
            else:
                self.root.after(self.stimulus_ms, lambda: self.ITI(None))

        # First Testing: 
        # If B+, send to reinforcement; if test trial, send to ITI
        elif self.exp_phase_num == 1: #Testing Phase
            if self.trial_type in ("B"):
                self.root.after(self.stimulus_ms, self.reinforcement_phase)
            else:
                self.root.after(self.stimulus_ms, lambda: self.ITI(None))
                
        # Extinction: 
        # If excitor, send to reinforcement; if inhibitor, send to ITI (differs by condition)
        elif self.exp_phase_num == 2: #Extinction Phase
            
            # No Extinction -- NOT USED IN CURRENT DESIGN
            if self.subject_ID in ["TEST"]:  
                if self.trial_type in ("A", "B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))

            # Extinction A 
            elif self.subject_ID in ["Luigi", "Mario", "Wenchang"]: 
                if self.trial_type in ("B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None)) 
          
            # Extinction C
            elif self.subject_ID in ["Joplin", "Thoth", "Durrell"]: 
                if self.trial_type in ("A", "B"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))

            # Extinction X
            elif self.subject_ID in ["Itzamna", "Odin", "Vonnegut"]: 
                if self.trial_type in ("B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))
                
        # Second Testing: 
        # If B+, send to reinforcement; if test trial, send to ITI
        elif self.exp_phase_num == 3: #Testing Phase
            if self.trial_type in ("B"):
                self.root.after(self.stimulus_ms, self.reinforcement_phase)
            else:
                self.root.after(self.stimulus_ms, lambda: self.ITI(None))
                
        # Recovery: 
        # If B+, send to reinforcement; if test trial, send to ITI
        elif self.exp_phase_num == 4: #Recovery Phase
            if self.trial_type in ("B"):
                self.root.after(self.stimulus_ms, self.reinforcement_phase)
            else:
                self.root.after(self.stimulus_ms, lambda: self.ITI(None))
 
        
    # Reinforcement for excitors
    def reinforcement_phase(self):
        self.trial_stage = 3
        # We first need to add one to the reinforcement counter
        self.reinforced_trial_counter += 1
        # In this part of a trial, reinforcement is provided
        self.clear_canvas()
        self.write_data(None, "reinforcement_provided")
        # Print text on screen if a test (should be black if an experimental trial)
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(512, 384,
                                      fill="white",
                                      font="Times 26 italic bold",
                                      text=f"Reinforcement TIME ({int(self.hopper_duration/1000)} s)")
        
    # Next send output to the box's hardware
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num,
                            False) # Turn off the house light
            rpi_board.write(hopper_light_GPIO_num,
                            True) # Turn off the hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_up_val) # Move hopper to up position
    # Check if this is the last trial
        if self.current_trial_counter == self.max_trials:
            self.root.after(self.hopper_duration, lambda: self.exit_program("event"))
        else:
            self.root.after(self.hopper_duration, lambda: self.ITI(None))

####Don't worry about for now -------------------------------------------------

    def _draw_stimulus_rects(self, trial_type: str):

        def draw_diamonds(stim_key):
            img = self.stimulus_images[stim_key]
            for slot in self.POSITIONS[stim_key]:
                cx, cy = self.DIAMOND_CENTERS[slot]
                self.mastercanvas.create_image(
                    cx, cy,
                    anchor="center",
                    image=img,
                    tags=("stimulus",)
                )

        if trial_type == "AX":
            draw_diamonds("A")   # top + bottom
            draw_diamonds("X")   # left + right
        elif trial_type == "BX":
            draw_diamonds("B")   # top + bottom
            draw_diamonds("X")   # left + right
        elif trial_type == "BY":
            draw_diamonds("B")   # top + bottom
            draw_diamonds("Y")   # left + right
        else:
            if trial_type in self.POSITIONS:
                draw_diamonds(trial_type)

# -----------------------------------------------------------------------------

    def change_cursor_state(self):
        # This function toggles the cursor state on/off. 
        # May need to update accessibility settings on your machince.
        if self.cursor_visible: # If cursor currently on...
            self.root.config(cursor="none") # Turn off cursor
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else: # If cursor currently off...
            self.root.config(cursor="") # Turn on cursor
            print("### Cursor turned on ###")
            self.cursor_visible = True                                    
    
    def clear_canvas(self):
         # This is by far the most called function across the program. It
         # deletes all the objects currently on the Canvas. A finer point to 
         # note here is that objects still exist onscreen if they are covered
         # up (rendering them invisible and inaccessible); if too many objects
         # are stacked upon each other, it can may be too difficult to track/
         # project at once (especially if many of the objects have functions 
         # tied to them. Therefore, its important to frequently clean up the 
         # Canvas by literally deleting every element.
        try:
            self.mastercanvas.delete("all")
        except TclError:
            print("No screen to exit")
        
    def exit_program(self, event): 
        # This function can be called two different ways: automatically (when
        # time/reinforcer session constraints are reached) or manually (via the
        # "End Program" button in the control panel or bound "esc" key).
            
        # The program does a few different things:
        #   1) Return hopper to down state, in case session was manually ended
        #       during reinforcement (it shouldn't be)
        #   2) Turn cursor back on
        #   3) Writes compiled data matrix to a .csv file 
        #   4) Destroys the Canvas object 
        #   5) Calls the Paint object, which creates an onscreen Paint Canvas.
        #       In the future, if we aren't using the paint object, we'll need 
        #       to 
        def other_exit_funcs():
            if operant_box_version:
                rpi_board.write(hopper_light_GPIO_num,
                                False) # turn off hopper light
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # set hopper to down state
                sleep(1) # Sleep for 1 s
                rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                            False)
                rpi_board.set_PWM_frequency(servo_GPIO_num,
                                            False)
                rpi_board.stop() # Kill RPi board
                # root.after_cancel(AFTER)
                if not self.cursor_visible:
                	self.change_cursor_state() # turn cursor back on, if applicable
            self.write_comp_data(True) # write data for end of session
            if self.root.winfo_exists():  # Check if the window still exists
                self.root.destroy()  # destroy Canvas
            print("\n GUI window exited")
            
        self.clear_canvas()
        other_exit_funcs()
        print("\n You may now exit the terminal and operater windows now.")
        if operant_box_version:
            polygon_fill.main(self.subject_ID) # call paint object                  
        
    def write_data(self, event, outcome):

        # Get event coordinates
        x, y = (event.x, event.y) if event is not None else ("NA", "NA")

        print(f"{outcome:>30} | x: {x:^3} y: {y:^3} | Stage: {self.trial_stage:^5} | {str(datetime.now() - self.start_time)}")

        # Trial time (excluding ITI)
        """
        trial_time = round((datetime.now() - self.trial_start - timedelta(milliseconds=self.ITI_duration)).total_seconds(), 5) if self.trial_start else "NA"
        """
        trial_time = (
            round((datetime.now() - self.stimulus_start_time).total_seconds(), 5)
            if self.stimulus_start_time is not None
            else
            round((datetime.now() - self.trial_start).total_seconds() - (self.ITI_duration / 1000), 5)
        )

        # Update counters based on event type
        
        if outcome == "target_peck":
            self.target_peck_counter += 1
        elif outcome == "background_peck":
            self.background_peck_counter += 1
        elif outcome == "pre_CS_peck":
            self.pre_CS_peck_counter += 1
            
        # Only count within-trial pecks (exclude ITI pecks)
        
        if outcome in ("target_peck", "background_peck"):
            self.total_peck_counter += 1

        # Append to session data
        self.session_data_frame.append([
            str(datetime.now() - self.start_time),      # SessionTime
            self.exp_phase_name,                             # Exp_Phase
            self.subject_ID,                            # Subject
            x,                                          # Xcord
            y,                                          # Ycord
            outcome,                                    # Event
            trial_time,                                 # TrialTime
            self.trial_stage,                           # TrialStage
            self.trial_type,                            # TrialType
            getattr(self, "target_peck_counter", "NA"), # SignTrackingPecks
            getattr(self, "background_peck_counter", "NA"),# BackgroundPeckNum
            getattr(self, "total_peck_counter", "NA"),  #TotalPeckCounter (Sign + Background pecks)
            getattr(self, "pre_CS_peck_counter", "NA"), #PreStimulusPecks
            self.current_trial_counter,                 # TrialNum
            self.reinforced_trial_counter,              # Reinforced_Trial_Num
            self.date,                                  # Date
        ])

        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord",	"Ycord", "Event",	
            "TrialTime", "TrialStage", "TrialType",	"SignTrackingPecks", "BackgroundPeckNum",
            "TotalPeckCount", "PreStimulusPecks", "TrialNum", "ReinforcedTrialNum", "Date"] 
    
    def write_comp_data(self, SessionEnded):
        # The following function creates a .csv data document. It is either 
        # called after each trial during the ITI (SessionEnded ==False) or 
        # one the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase. Consecutive iterations of the function will simply
        # write over the existing document.
        if SessionEnded:
            self.write_data(None, "SessionEnds") # Writes end of session to df
        if self.record_data : # If experimenter has choosen to automatically record data in seperate sheet:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P042a.iii_data-{self.exp_phase_name}Phase.csv" # location of written .csv
            
            # This loop writes the data in the matrix to the .csv              
            edit_myFile = open(myFile_loc, 'w', newline='')
            with edit_myFile as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame) # Write all event/trial data 
                
            print(f"\n- Data file written to {myFile_loc}")
        
#%% Finally, this is the code that actually runs:
try:   
    if __name__ == '__main__':
        cp = ExperimenterControlPanel()
except:
    # If an unexpected error, make sure to clean up the GPIO board
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                    False)
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    False)
        rpi_board.stop()
