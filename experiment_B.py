"""
VERSION B - discriminating weak index and ring finger targets following three salient rhythm-establishing stimuli presented to both fingers
"""

from pathlib import Path
from typing import Union

# local imports
from utils.experiment import Experiment
from utils.SGC_connector import SGCConnector, SGCFakeConnector

class Experiment_B(Experiment):
    def __init__(
            self, 
            trigger_mapping: dict,
            mean_ISI:float = 1.45,
            order = [0, 1, 0, 2, 1, 0, 2, 1, 0 ,2, 0, 1],
            n_sequences: int = 10, 
            resp_n_sequences:int = 3, 
            prop_left_right: list = [0.5, 0.5], 
            intensities = {"salient": 6.0, "weak": 2.0},
            trigger_duration = 0.001, 
            QUEST_target: float = 0.75,
            reset_QUEST: Union[int, bool] = False, # how many blocks before resetting QUEST
            QUEST_plus: bool = True,
            ISI_adjustment_factor: float = 0.1,
            logfile: Path = Path("data.csv"),
            SGC_connectors = None
            ):
        
        super().__init__(
            trigger_mapping = trigger_mapping,
            mean_ISI = mean_ISI,
            order = order,
            n_sequences = n_sequences,
            resp_n_sequences = resp_n_sequences,
            prop_target1_target2 = prop_left_right,
            target_1="left",
            target_2="right",
            intensities = intensities,
            trigger_duration = trigger_duration,
            QUEST_target = QUEST_target,
            reset_QUEST = reset_QUEST,
            QUEST_plus = QUEST_plus,
            ISI_adjustment_factor = ISI_adjustment_factor,
            logfile = logfile)
            
        self.SGC_connectors = SGC_connectors
    
    def deliver_stimulus(self, event_type):
        if self.SGC_connectors: 
                if "salient" in event_type: # send to both fingers
                    for connector in self.SGC_connectors.values():
                        connector.send_pulse()
                elif self.SGC_connectors and "target" in event_type: # send to the finger specified in the event type
                    self.SGC_connectors[event_type.split("/")[-1]].send_pulse()

    def prepare_for_next_stimulus(self, event_type, next_event_type):
        if self.SGC_connectors:
            # after sending the trigger for the weak target stimulation change the intensity to the salient intensity
            if "target" in event_type: 
                self.SGC_connectors[event_type.split("/")[-1]].change_intensity(self.intensities["salient"])

            # check if next stimuli is weak, then lower based on which!
            if "target" in next_event_type:
                self.SGC_connectors[next_event_type.split("/")[-1]].change_intensity(self.intensities["weak"])

    

if __name__ == "__main__":

    stim_bit = 1
    target_bit = 2
    right_bit = 4
    left_bit = 8
    response_bit = 16
    correct = 32
    incorrect = 64

    trigger_mapping= {
        "stim/salient": stim_bit,
        "target/right": target_bit + right_bit,  
        "target/left": target_bit + left_bit,
        "response/left/correct": response_bit + left_bit + correct,
        "response/right/incorrect": response_bit + right_bit + incorrect, 
        "response/right/correct": response_bit + right_bit + correct,
        "response/left/incorrect": response_bit + left_bit + incorrect, 
        }
    
    start_intensities = {"salient": 4.0, "weak": 1.0} # SALIENT NEEDS TO BE AT LEAST xx BIGGER THAN 


    connectors = {
        "left":  SGCConnector(port="/dev/tty.usbserial-5", intensity_codes_path=Path("intensity_code.csv"), start_intensity=1),
        "right": SGCFakeConnector(intensity_codes_path=Path("intensity_code.csv"), start_intensity=1)
    }

    for side, connector in connectors.items():
        connector.set_pulse_duration(200)
        connector.change_intensity(start_intensities["salient"])
    

    experiment = Experiment_B(
        intensities=start_intensities,
        n_sequences=5,
        reset_QUEST=3, # reset QUEST every x blocks
        mean_ISI=1.39,
        trigger_mapping=trigger_mapping,
        logfile = Path("output_b/test_SGC.csv"),
        SGC_connectors=connectors
    )
    
    duration = experiment.estimate_duration()
    print(f"The experiment is estimated to last {duration} seconds")

    experiment.run()
