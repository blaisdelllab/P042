#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 11:18:48 2025

@author: marisacalarco & kayleyozimac

Last updated 2025-12-11

#This is the code for the 'Extinction of Conditioned Inhibition' project (P042) 

This is an adjacent replication of P021, an off shoot of the 'Suboptimal Choice Task' study


Training Phase: We will begin with excitation training of stimuli A, B, and C along with
inhibition training of AX, and exposure to Y (4 trials in one of the sessions, TBD when) **
    Trials begin with an 10s ITI
    Stimulus A, B, C, AX, or Y is then presented for 30s 
        Stimulus order is randomized
    A, B, and C trials are followed by food reward (5s)
    AX and Y trials are never followed by food reward
    Process repeats 


Extinction Phase: We will divide subjects into four equal sized groups, which will 
undergo unique extinction procedures,  
    Group No-Extinction: No excinction training, presentations of A+, B+, C+ (A+/B+/C+)
    Group Extinction A: Extcinction training of A, B+ and C+ presentattions  (A-/B+/C+)
    Group Extinction X: Extinction training of X, B+ and C+ presentations  (X-/B+/C+)
    Group Extinction C: Extinction training of C, A+ and B+ presentations  (A+/B+/C-)
    
    
Testing Phase: We will test stimuli B, BX, and BY interspersed with C+ presentations
B and BX serve as a summation test, while BY serves as a control for external inhibition


Recovery phase: After 3 weeks, we will test stimulus A to evaluate if spontaneous
recovery has occured for the excitor, for the Extinction A group. If recovery is
observed, we will then test AX, B, and BX, again with interspersed C+ trials.
If recovery is not observed, we will re-excite A+ in a second training phase, 
before completing testing 

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
        self.control_window.title("P042a Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Thoth", "Joplin", "Odin", "Mario", "Jagger", "Luigi", "Wenchang", "Itzamna"]
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
                                          "Phase 2 (Extinction)",
                                          "Phase 3 (Testing)"]
        
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
            self.exp_phase_name = "Phase 2 (Extinction)"
        if self.exp_phase_num == 2:
            self.exp_phase_name = "Phase 3 (Testing)"
            
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
            self.ITI_duration = 3000
        else: 
            self.ITI_duration = 10000
        if not operant_box_version or self.subject_ID == "TEST":
            self.hopper_duration = 3000
        else:
            self.hopper_duration = 5000
        
        self.reinforced_trial_counter = 0
        self.last_written_trial_num = None
        if self.exp_phase_num == 0:
            self.max_number_of_trials = 100 # 104 when we have exposure Y session
        else:
            self.max_number_of_trials = 90
            
        self.session_data_frame = []
        self.trial_stage = 0
        self.current_trial_counter = 0
        self.trial_type = []
        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord",	"Ycord", "Event",	
            "TrialTime", "TrialStage", "TrialType",	"SignTrackingPecks", "BackgroundPeckNum",
            "TotalPeckCount", "TrialNum", "ReinforcedTrialNum", "Date"] 
        self.session_data_frame.append(header_list)
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL'
        
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
                                      text=f"P042a \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase: {self.exp_phase_name}")

    def first_ITI(self, event):
        print("Spacebar pressed -- SESSION STARTED") 
        
        self.trial_stage = 0 #First substage
    
        # Trial assignment for training
        
        if self.exp_phase_num == 0: #Training Phase
            
           # Core training cues per spec: A+/B+/C+, AX-
            
           # Training trial proportions:
           # 100 total trials (20 blocks of 5)
           # Each block: 2 AX-, 1 A+, 1 B+, 1 C+ (randomized order per block)
           
            self.trial_types = ["A", "B", "C", "AX"]
           
           # Define block composition and total trials
            trial_blocks = ["AX", "AX", "A", "B", "C"]
            n_blocks = 20  # 20 blocks × 5 trials = 100 total
           
            self.trial_assignment_list = []
           
            for _ in range(n_blocks):
               block = trial_blocks[:]  
               shuffle(block)        # randomize order within block
               self.trial_assignment_list.extend(block)
            

        # Optional: add 4 Y exposures in first session (leave False all other days)
            include_Y_this_session = False
            if include_Y_this_session:
                # Insert 4 Y-trials, one in each 25-trial block
                import random
                
                # Block boundaries: 0–24, 25–49, 50–74, 75–99
                block_ranges = [
                    (0, 24),
                    (25, 49),
                    (50, 74),
                    (75, 99),
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
          

        elif self.exp_phase_num == 1: # Extinction Phase
        # Build trial lists for Group No Extinction, Extinction A, Extincion X
            
            if self.subject_ID in ["Joplin", "Odin", "Wenchang", "Thoth", "Mario", "Itzamna", "TEST"]: 
                self.trial_types = ["A", "B", "C"]
            # Build trial list for Group Extinction X
            elif self.subject_ID in ["Jagger", "Luigi"]: 
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
            
        
        elif self.exp_phase_num == 2: # Testing Phase
            self.trial_types = ["B", "BX", "BY"] 
            
           # Testing trial proportions:
               # 20 total trials (4 blocks of 5)
               # Each block: 3 B+, 1 BX-, 1 BY- (randomized order per block)

            self.trial_types = ["B", "BX", "BY"]

            # Define block composition and total trials
            trial_blocks = ["B", "B", "B", "BX", "BY"]
            n_blocks = 4  # 4 blocks × 5 trials = 20 total

            self.trial_assignment_list = []

            for _ in range(n_blocks):
                block = trial_blocks[:]  
                shuffle(block)        # randomize order within block
                self.trial_assignment_list.extend(block)
            
            # Update trial count
            self.max_trials = len(self.trial_assignment_list)
            
            # Confirm trial list built correctly 
            print(f"Counts: { {stim: self.trial_assignment_list.count(stim) for stim in self.trial_types} }")
            print(f"Testing trial list ({self.max_trials}): {self.trial_assignment_list}")  
        
    
        # Session timing constants
        self.stimulus_ms = 30000
        # Excitor vs. inhibitor reinfrocement mappings
        self.reinforce_map = {"A": True, "B": True, "C": True, "AX": False, "Y": False}
    
        # Visual spec carried over from your demo
        if self.subject_ID in ["Joplin", "Odin", "Wenchang", "Jagger", "TEST"]: 
            self.COLORS = {
                "A": "#D11C00",
                "B": "#D10099",
                "C": "#7D00D1",
                "X": "#0023D1",
                "Y": "#D1AE00"
        }
        elif self.subject_ID in ["Thoth", "Mario", "Luigi", "Itzamna"]:
            self.COLORS = {
                "A": "#D11C00",
                "B": "#D10099",
                "C": "#7D00D1",
                "X": "#D1AE00",
                "Y": "#0023D1"
            }
        self.POSITIONS = {
            "A": [(0, 1), (1, 0)],
            "B": [(0, 1), (1, 0)],
            "C": [(0, 1), (1, 0)],
            "X": [(0, 0), (1, 1)],
            "Y": [(0, 0), (1, 1)]
        }
        self.SQUARE_SIZE = 55 
        self.GAP = 10 
        cx, cy = self.mainscreen_width // 2, self.mainscreen_height // 2
        self.ORIGIN_X = cx - 60
        self.ORIGIN_Y = cy - 58
        
        #Housekeeping
        
        self.current_trial_counter = 0 
        self.root.unbind("<space>") # bind cursor state to "space" key
        self.clear_canvas()
        self.start_time = datetime.now()  # This is the ACTUAL time the session starts
        self.target_peck_counter = 0
        self.background_peck_counter = 0
        self.total_peck_counter = 0  
        
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
        
        # Write last trial’s data
        # self.write_comp_data(False)
        
        # Reset ITI duration after the first trial
        if not operant_box_version or self.subject_ID == "TEST":
            self.ITI_duration = 3000
        else:
            self.ITI_duration = 10000

        # Print headers and trial-type info
        print(f"\n{'*' * 30} Trial {self.current_trial_counter} begins {'*' * 30}")
        print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")
        
        self.root.after(self.ITI_duration, self.stimulus_phase)


    
    def stimulus_phase(self, event=None):
        
        """Present the current trial's stimulus for self.stimulus_ms, log pecks."""
        
        self.clear_canvas()
    
        # Full-screen background (logs background_peck)
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, 
            self.mainscreen_height,
            fill="black",
            outline="black", 
            tag="bkgrd"
        )
        
        # Black square receptive field:
        receptivefield_size = 150  # adjust this to control square size (in pixels)
        x_center = self.mainscreen_width / 2
        y_center = self.mainscreen_height / 2
        
        self.mastercanvas.create_rectangle(
            x_center - receptivefield_size / 2,
            y_center - receptivefield_size / 2,
            x_center + receptivefield_size / 2,
            y_center + receptivefield_size / 2,
            fill="black", # 
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
        self.trial_stage = 1  # stimulus on
        self.trial_start = datetime.now()
        self.stimulus_start_time = datetime.now()
    
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
                
        # Extinction: 
        # If excitor, send to reinforcement; if inhibitor, send to ITI (differs by condition)
        elif self.exp_phase_num == 1: #Extinction Phase
            
            # No Extinction
            if self.subject_ID in ["Wenchang", "Itzamna", "TEST"]:  
                if self.trial_type in ("A", "B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))
        
            # Extinction A 
            elif self.subject_ID in ["Joplin", "Thoth"]: 
                if self.trial_type in ("B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None)) 
          
            # Extinction C
            elif self.subject_ID in ["Odin", "Mario"]: 
                if self.trial_type in ("A", "B"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))

            # Extinction X
            elif self.subject_ID in ["Jagger", "Luigi"]: 
                if self.trial_type in ("B", "C"):
                    self.root.after(self.stimulus_ms, self.reinforcement_phase)
                else:
                    self.root.after(self.stimulus_ms, lambda: self.ITI(None))
                
        # Testing: 
        # If B+, send to reinforcement; if test trial, send to ITI
        elif self.exp_phase_num == 2: #Testing Phase
            if self.trial_type in ("B"):
                self.root.after(self.stimulus_ms, self.reinforcement_phase)
            else:
                self.root.after(self.stimulus_ms, lambda: self.ITI(None))
 
        
    # Reinforcement for excitors
    def reinforcement_phase(self):
        self.trial_stage = 2
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
        """
        Draw the colored squares for A/B/C/X/Y or the AX compound
        on top of the per-cell black 'stimulus' bases.
        """
        def cell_to_xy(r, c):
            x1 = self.ORIGIN_X + c * (self.SQUARE_SIZE + self.GAP)
            y1 = self.ORIGIN_Y + r * (self.SQUARE_SIZE + self.GAP)
            return x1, y1, x1 + self.SQUARE_SIZE, y1 + self.SQUARE_SIZE
    
        if trial_type == "AX":
            # A first
            for r, c in self.POSITIONS["A"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["A"], outline="", tags=("stimulus",)
                )
            # X overlay
            for r, c in self.POSITIONS["X"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["X"], outline="", tags=("stimulus",)
                )
    
        if trial_type == "BX":
            # A first
            for r, c in self.POSITIONS["B"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["B"], outline="", tags=("stimulus",)
                )
            # X overlay
            for r, c in self.POSITIONS["X"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["X"], outline="", tags=("stimulus",)
                )
        if trial_type == "BY":
            # A first
            for r, c in self.POSITIONS["B"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["B"], outline="", tags=("stimulus",)
                )
            # X overlay
            for r, c in self.POSITIONS["Y"]:
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=self.COLORS["Y"], outline="", tags=("stimulus",)
                )
        else:
            color = self.COLORS.get(trial_type, "#FFFFFF")
            for r, c in self.POSITIONS.get(trial_type, []):
                self.mastercanvas.create_rectangle(
                    *cell_to_xy(r, c),
                    fill=color, outline="", tags=("stimulus",)
                )
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
            self.current_trial_counter,                 # TrialNum
            self.reinforced_trial_counter,              # Reinforced_Trial_Num
            self.date,                                  # Date
        ])

        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord",	"Ycord", "Event",	
            "TrialTime", "TrialStage", "TrialType",	"SignTrackingPecks", "BackgroundPeckNum",
            "TotalPeckCount", "TrialNum", "ReinforcedTrialNum", "Date"] 
    
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
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P042a_data-{self.exp_phase_name}Phase.csv" # location of written .csv
            
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