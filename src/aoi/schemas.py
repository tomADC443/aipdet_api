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
