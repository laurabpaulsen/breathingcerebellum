"""
VERSION A - discriminating weak and omission targets following three salient rhythm-establishing stimuli 
NOTES: do we want to record button presses outside of the target window? Sanity check for the experiment? 
"""

from pathlib import Path
from utils.experiment import Experiment
import time
from typing import Union
import numpy as np
from utils.SGC_connector import SGC_connector



class Experiment_A(Experiment):
    def __init__(
            self, 
            trigger_mapping: dict,
            mean_ISI:float = 1.5,
            order = [0, 1, 0, 2, 1, 0, 2, 1, 0 ,2, 0, 1],
            n_sequences: int = 10, 
            resp_n_sequences:int = 3, 
            prop_weak_omis: list = [0.9, 0.1], 
            intensities = {"salient": 6.0, "weak": 2.0},
            trigger_duration = 0.001, 
            QUEST_target: float = 0.75,
            reset_QUEST: Union[int, bool] = False, # how many blocks before resetting QUEST
            QUEST_plus: bool = True,
            ISI_adjustment_factor: float = 0.1,
            logfile: Path = Path("data.csv"),
            SGC_connector = None
            ):
        
        super().__init__(
            trigger_mapping = trigger_mapping,
            mean_ISI = mean_ISI,
            order = order,
            n_sequences = n_sequences,
            resp_n_sequences = resp_n_sequences,
            prop_target1_target2 = prop_weak_omis,
            target_1="weak",
            target_2="omis",
            intensities = intensities,
            trigger_duration = trigger_duration,
            QUEST_target = QUEST_target,
            reset_QUEST = reset_QUEST,
            QUEST_plus = QUEST_plus,
            ISI_adjustment_factor = ISI_adjustment_factor,
            logfile = logfile)
        
        self.SGC_connector = SGC_connector


    def deliver_stimulus(self, event_type):
        if self.SGC_connector and "omis" not in event_type: 
            self.SGC_connector.send_pulse()

    def prepare_for_next_stimulus(self, event_type, next_event_type):
        if event_type == "target/weak": # after sending the trigger for the weak target stimulation change the intensity to the salient intensity
            self.SGC_connector.change_intensity(self.intensities["salient"])

        if next_event_type == "target/weak":
                self.SGC_connector.change_intensity(self.intensities["weak"])
    
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
        port = "/dev/tty.usbserial-A50027Ed",
        intensity_codes_path=Path("intensity_code.csv"),
        start_intensity=1
    )

    connector.set_pulse_duration(200)
    #connector.set_trigger_delay(0)


    experiment = Experiment_A(
        n_sequences=5,
        reset_QUEST=3, # reset QUEST every x blocks
        mean_ISI=1.,
        trigger_mapping=trigger_mapping,
        logfile = Path("output_a/test_SGC.csv"),
        SGC_connector=connector
    )
    
    duration = experiment.estimate_duration()
    print(f"The experiment is estimated to last {duration} seconds")

    experiment.run()
