from pydantic import BaseModel, Field
from typing import List


class PolygonInputSchema(BaseModel):
    # Enforce the GeoJSON Feature type
    type: str = Field("Feature", const=True)
    geometry: dict
    coordinates: List[List[List[float]]
                      ] = Field(..., description="Polygon coordinates")

    @property
    def geometry(self):
        return {
            "type": "Polygon",
            "coordinates": self.coordinates,
        }
