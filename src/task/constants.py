from enum import Enum


class Task_Status(Enum):
    Successful = "Successful"
    Failed = "Failed"
    Processing = "Processing"


final_states = [Task_Status.Successful.value, Task_Status.Failed.value]
