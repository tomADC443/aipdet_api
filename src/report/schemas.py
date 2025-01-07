from fastapi import Query


task_id_parameter = Query(
    ...,
    alias="taskId",
    min_length=1,
    max_length=100,
    examples=["1-023948-9182374"],
    description="Id of the task in question."
)
