from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_geojson import FeatureModel  # type: ignore
from fastapi import Query


class CustomFeatureModel(FeatureModel):
    properties: Optional[dict] = Field(
        default=None,
        description="Optional properties for the GeoJSON feature."
    )  # type: ignore


class AOICreationRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100,
        examples=["My Area of Interest"],
        description="The name of the AOI (Area of Interest)."
    )
    description: str = Field(
        None, max_length=500,
        examples=["This is a sample area of interest for mapping."],
        description="An optional description of the AOI."
    )
    geometry: CustomFeatureModel = Field(
        ...,
        description="The geometry of the AOI as a GeoJSON Feature object."
    )


class AOIDeletionRequest(BaseModel):
    id: str = Field(
        ..., min_length=1, max_length=100,
        examples=["987987-9879"],
        description="The id of the AOI (Area of Interest) that should be deleted."
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
    geometry: CustomFeatureModel = Field(
        ...,
        description="The geometry of the AOI as a GeoJSON Feature object."
    )


class AoiGetResponse(BaseModel):
    aois: List[AOI] = Field(
        ...,
        description="A list of AOIs."
    )


aoi_id_parameter = Query(
    ...,
    alias="id",
    min_length=1,
    max_length=100,
    examples=["1-023948-9182374"],
    description="Id of the aoi in question."
)
