"""
NOTES: do we want to record button presses outside of the target window? Sanity check for the experiment? 
"""

from pathlib import Path
import time
from tqdm import tqdm
from triggers import setParallelData
from psychopy.clock import CountdownTimer
from psychopy.data import QuestHandler
from numpy.random import choice
from pynput import keyboard  # Import pynput for keyboard handling
from typing import Union

from .SGC_connector import SGC_connector


class Experiment:
    def __init__(
            self, 
            ISIS = [None, 1.5, None], 
            order = [0, 1, 0, 2, 1, 0, 2, 1, 0 ,2, 0, 1],
            n_sequences: int = 10, 
            prop_weak_omis: list = [0.9, 0.1], 
            trigger_mapping: dict = {
                "target/weak": 100, "stim/salient": 2, "target/omis": 200, 
                "response/left": 1000, "response/right": 1000,
            },
            QUEST_target: float = 0.75,
            QUEST_start_val = 2,
            trigger_duration = 0.001, 
            reset_QUEST: Union[int, bool] = False, # how many blocks before resetting QUEST
            ISI_adjustment_factor: float = 0.1,
            logfile: Path = Path("data.csv"),
            SGC_connector: SGC_connector = None
            ):
        """
        
        
        """
        
        self.ISIs = ISIS
        self.reset_QUEST = reset_QUEST
        self.logfile = logfile
        self.n_sequences = n_sequences
        self.order = order
        self.trigger_mapping = trigger_mapping
        self.prop_weak_omis = prop_weak_omis
        self.trigger_duration = trigger_duration
        self.countdown_timer = CountdownTimer() 
        self.events = []

        self.ISI_adjustment_factor = ISI_adjustment_factor
        
        
        # for response handling 
        self.key_pressed = None  # Variable to store the last key pressed
        self.listener = None  # Keyboard listener instance
        self.target_active = False  # Flag to check if target stimulus is active
        self.keys_target = {
            "omis": ['2', 'y'],
            "weak": ['1', 'b']
        }
        
        # QUEST parameters
        self.QUEST_start_val = QUEST_start_val 
        self.intensities =  {"salient": 4, "weak": self.QUEST_start_val} # NOTE: do we want to reset QUEST with the startvalue or start from a percentage of the weak intensity stimulation?
        self.QUEST_target = QUEST_target 
        self.QUEST_reset()
        self.update_weak_intensity()
        self.SGC_connector = SGC_connector

    def setup_experiment(self):
        for block_idx, block in enumerate(self.order):
            ISI = self.ISIs[block]

            # check if QUEST needs to be reset in this block
            if self.reset_QUEST and block_idx % self.reset_QUEST == 0 and block_idx != 0:
                reset = int( self.n_sequences/2) # half way through the block
                print(block_idx, reset)
            else:
                reset = False
        
            self.events.extend(self.event_sequence(self.n_sequences, ISI, self.prop_weak_omis, block_idx, reset_QUEST=reset))
        
    def event_sequence(self, n_sequences, ISI, prop_weak_omis, block_idx, n_salient=3, reset_QUEST: Union[int, None] = None) -> list[dict]:
        """
        Generate a sequence of events for a block

        reset_QUEST: int or None
            If an integer, the QUEST procedure will be reset after this many sequences
        """
        event_counter_in_block = 0

        events = []
        for seq in range(n_sequences):
            for _ in range(n_salient):
                event_counter_in_block += 1
                events.append({"ISI": ISI, "type": "stim/salient", "n_in_block": event_counter_in_block, "block": block_idx, "reset_QUEST": False})
            
            event_counter_in_block += 1
            event_type = choice(["weak", "omis"], 1, p=prop_weak_omis)
            
            if reset_QUEST and seq == reset_QUEST:  
                reset = True
                
            else:
                reset = False
            events.append({"ISI": ISI, "type": f"target/{event_type[0]}", "n_in_block": event_counter_in_block, "block": block_idx, "reset_QUEST": reset})

        return events


    def determine_respiratory_rate(self, start_time, log_file):
        """
        Runs a set of sequences with same ISI as block B to determine respiratory rate during task
        """

        events = self.event_sequence(3, self.ISIs[1], self.prop_weak_omis, block_idx = "det_respiratory_rate")

        self.loop_over_events(events, start_time, log_file)

        # get input from user on respiratory rate
        respiratory_rate = self.get_user_input_respiratory_rate()

        # update ISI for block A and C (-+ 10 percent of the respiratory rate of block B)
        self.adjust_ISI(respiratory_rate)

    def get_user_input_respiratory_rate(self):
        while True:
            try:
                respiratory_rate = float(input("Please input the respiratory rate: "))
                if respiratory_rate <= 0:
                    print("Invalid input. Please enter a positive value.")
                else: 
                    break
            except ValueError:
                print("Invalid input. Please enter a numeric value.")

        return respiratory_rate

    def adjust_ISI(self, rate):
        """
        Adjust ISI for block A and C based on respiratory rate in block B and respiratory rate
        """
        self.ISIs[0] = self.ISIs[1] - self.ISI_adjustment_factor * rate
        self.ISIs[2] = self.ISIs[1] + self.ISI_adjustment_factor * rate

        print(f"ISI for block A: {self.ISIs[0]}, ISI for block C: {self.ISIs[2]} after adjustment based on respiratory rate {rate}")
    
    def log_event(self, event_time, block, ISI, intensity, event_type, trigger, n_in_block, correct, log_file):
            log_file.write(f"{event_time},{block},{ISI},{intensity},{event_type},{trigger},{n_in_block},{correct}\n")

    
    def loop_over_events(self, events: list[dict], start_time: float, log_file):
        for trial in tqdm(events):
            trigger = self.trigger_mapping[trial["type"]]
            ISI = trial["ISI"]
            n_in_block = trial["n_in_block"]
            intensity = self.intensities.get(trial["type"].split('/')[1], 0)

            event_time = time.perf_counter() - start_time
            self.raise_and_lower_trigger(trigger)  # Send trigger
            self.log_event(
                event_time = event_time, 
                block=trial['block'], 
                ISI=trial['ISI'], 
                intensity=intensity, 
                event_type=trial["type"], 
                trigger=trigger,
                n_in_block= n_in_block, 
                correct="NA", log_file = log_file
                )
            print(f"Event: {trial['type']}, intensity: {intensity}")

            # Check if this is a target event
            self.target_active = "target" in trial["type"]

            target_time = event_time + ISI + start_time
            response_given = False # to keep track of whether a response has been given
    
            while time.perf_counter() < target_time:
                # check for key press during target window
                if self.target_active and not response_given:
                    key = self.get_response()
                    if key:
                        correct, response_trigger = self.correct_or_incorrect(key, trial["type"])
                        print(f"Response: {key}, Correct: {correct}")
                        self.raise_and_lower_trigger(response_trigger) 
                        response_given = True
                        self.log_event(
                            event_time=time.perf_counter() - start_time, 
                            block=trial['block'], 
                            ISI=trial['ISI'], 
                            intensity=intensity, 
                            event_type="response", 
                            trigger=response_trigger, 
                            n_in_block=n_in_block, 
                            correct=correct, 
                            log_file = log_file
                            )
                        
                        if trial["type"] == "target/weak":
                            self.QUEST.addResponse(correct, intensity = intensity)

                            # update intensities based on QUEST
                            self.update_weak_intensity()

                        # check if QUEST should be reset
                        if trial["reset_QUEST"]:
                            self.QUEST_reset()
                            print("QUEST has been reset")
                            self.update_weak_intensity()

            # Reset the target flag after the ISI
            self.target_active = False


    def raise_and_lower_trigger(self, trigger):
        setParallelData(trigger)
        self.countdown_timer.reset(self.trigger_duration)
        while self.countdown_timer.getTime() > 0:
            pass
        setParallelData(0)

    def on_press(self, key):
        """Callback for key press events."""
        try:
            key_name = key.char  # alphanumeric keys
        except AttributeError:
            key_name = str(key)  # special keys
        if self.target_active and key_name in ['1', '2', 'y', 'b']:  # only capture specific keys during target
            self.key_pressed = key_name

    def start_listener(self):
        """Start the keyboard listener."""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop_listener(self):
        """Stop the keyboard listener."""
        if self.listener:
            self.listener.stop()

    def get_response(self):
        """Retrieve the last key pressed and reset the key state."""
        response = self.key_pressed
        self.key_pressed = None  # Reset after capturing
        return response
    
    def correct_or_incorrect(self, key, event_type):
        if key in self.keys_target[event_type.split('/')[1]]:
            return 1, self.trigger_mapping[f"response/{event_type.split('/')[1]}/correct"]
        else:
            return 0, self.trigger_mapping[f"response/{event_type.split('/')[1]}/incorrect"]

    def QUEST_reset(self):
        """Reset the QUEST procedure."""
        self.QUEST = QuestHandler(
            startVal=self.QUEST_start_val,  # Initial guess for intensity
            startValSd=0.2,  # Standard deviation
            minVal=0,
            maxVal=4,
            pThreshold=self.QUEST_target,  # Target probability threshold (e.g., 75% detection)
            stepType = "log",
            nTrials=None,  # Total number of trials
            beta=3.5,  # Slope of the psychometric function
            gamma=0.5,  # Guess rate (e.g., 50% for a 2-alternative forced choice task)
            delta=0.01  # Lapse rate (probability of missing a stimulus even if it's detectable)
        )


    def update_weak_intensity(self):
        """
        Update the weak intensity based on the QUEST procedure!
        """
        proposed_intensity = self.QUEST.next()
        

        ## NOTE: GET THE CLOSEST VALUE THAT IS POSSIBLE WITH SCG and update

        self.intensities["weak"] = proposed_intensity 

        #if len(self.correct) > 0:
        #    p_correct = sum(self.correct) / len(self.correct)
        #    if p_correct > self.QUEST_target:
        #        self.intensities["weak"] += 0.02
        #    else:
        #        self.intensities["weak"] -= 0.02


    def run(self):
        self.start_listener()  # Start the keyboard listener
        self.logfile.parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

        start_time = time.perf_counter()
       
        with open(self.logfile, 'w') as log_file:
            log_file.write("time,block,ISI,intensity,event_type,trigger,n_in_block,correct\n")
            
            # determine the respiratory rate during block B
            self.determine_respiratory_rate(start_time, log_file)

            # run the experiment
            self.setup_experiment()
            self.loop_over_events(self.events, start_time, log_file)

        self.stop_listener()  # Stop the keyboard listener

if __name__ == "__main__":

    stim_bit = 1
    target_bit = 2
    weak_bit = 4
    omis_bit = 8
    response_bit = 16
    correct = 32
    incorrect = 64

    trigger_mapping= {
        "stim/salient": stim_bit,
        "target/weak": target_bit + weak_bit,  
        "target/omis": target_bit + omis_bit,
        "response/omis/correct": response_bit + omis_bit + correct,
        "response/omis/incorrect": response_bit + weak_bit + incorrect, 
        "response/weak/correct": response_bit + weak_bit + correct,
        "response/weak/incorrect": response_bit + omis_bit + incorrect, 
        }


    # connect to the stimulus current generator
    connector = SGC_connector(
        intensity_codes_path=Path("intensity_code.csv"),
        start_intensity=1
    )

    connector.set_pulse_duration(200)
    connector.set_trigger_delay(0)


    experiment = Experiment(
        n_sequences=10,
        reset_QUEST=3, # reset QUEST every x blocks
        ISIS=[None, 0.7, None],
        trigger_mapping=trigger_mapping,
        prop_weak_omis=[0.9, 0.1],
        logfile = Path("output/test.csv"),
        #SGC_connector=connector
    )
    
    experiment.run()
