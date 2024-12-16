from typing import List, Literal
from pydantic import BaseModel, Field


class Geometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]] = Field(
        ...,
        description="A list of linear ring coordinates defining the polygon. The first and last point of each ring must be the same."
    )


class Properties(BaseModel):
    pass


class GeoJSONPolygonFeature(BaseModel):
    type: Literal["Feature"]
    geometry: Geometry
    properties: Properties
