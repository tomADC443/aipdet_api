from typing import List
from pydantic import BaseModel, Field
from pydantic_geojson import FeatureModel


class AOICreationRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100,
        example="My Area of Interest",
        description="The name of the AOI (Area of Interest)."
    )
    description: str = Field(
        None, max_length=500,
        example="This is a sample area of interest for mapping.",
        description="An optional description of the AOI."
    )
    geometry: FeatureModel = Field(
        ...,
        description="The geometry of the AOI as a GeoJSON Feature object."
    )


class AOI(BaseModel):
    id: str = Field(
        ...,
        description="The unique identifier of the AOI."
    )
    name: str = Field(
        ...,
        description="The name of the AOI."
    )
    description: str = Field(
        None,
        description="An optional description of the AOI."
    )
    createdAt: int = Field(
        ...,
        description="The timestamp when the AOI was created."
    )
    geometry: FeatureModel = Field(
        ...,
        description="The geometry of the AOI as a GeoJSON Feature object."
    )


class AoiGetResponse(BaseModel):
    aois: List[AOI] = Field(
        ...,
        description="A list of AOIs."
    )
