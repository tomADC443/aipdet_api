from pydantic import BaseModel, Field


class TaskCreationRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=50,
        examples=["My Area of Interest"],
        description="The name of the Task"
    )
    aoiId: str = Field(
        ..., min_length=1, max_length=100,
        examples=["fa39a5d2-caf4-4101-8d6d-b1b74f23s83 "],
        description="Identifier of the AOI that is associated to this Task"
    )
    isPublic: bool = Field(
        ...,
        description="A Boolean flag specifying if the Current route is pivate or public (can be seen by other users)"
    )


class TaskDeletionRequest(BaseModel):
    id: str = Field(
        ..., min_length=1, max_length=100,
        examples=["1234-47654"],
        description="The id of the Task that should be deleted."
    )
