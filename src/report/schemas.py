
from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from fastapi import Query
from pydantic_geojson import FeatureModel


task_id_parameter = Query(
    ...,
    alias="taskId",
    min_length=1,
    max_length=100,
    examples=["1-023948-9182374"],
    description="Id of the task in question."
)
dateString = Query(
    ...,
    alias="dateString",
    min_length=10,
    max_length=10,
    examples=["2020-05-21"],
    description="String representation of a date in the format YYYY-MM-DD."
)


class DistinctImagesResponse(BaseModel):
    count: int = Field(..., description="Total count of distinct images")


class TemporalRangeResponse(BaseModel):
    fromDate: datetime = Field(..., description="Start date of temporal range")
    toDate: datetime = Field(..., description="End date of temporal range")


class TotalAreaResponse(BaseModel):
    area: float = Field(...,
                        description="Total observed area in square kilometers")


class MonthlyAverage(BaseModel):
    month: List[str] = Field(..., description="List of month abbreviations")
    values: List[float] = Field(...,
                                description="List of corresponding NDVI values")


class WeeklyChanges(BaseModel):
    weeks: List[int] = Field(..., description="List of week numbers")
    values: List[Optional[float]
                 ] = Field(..., description="List of NDVI changes per week")


class ChangeMetrics(BaseModel):
    week: str = Field(..., description="Week number")
    week_description: str = Field(...,
                                  description="Description of the week period")
    change: str = Field(..., description="Numerical change in NDVI")
    change_percentage: str = Field(...,
                                   description="Percentage change in NDVI")


class GrowthRateResponse(BaseModel):
    weekly_changes: WeeklyChanges
    max_increase: ChangeMetrics
    max_decrease: ChangeMetrics


class Season(BaseModel):
    season_start_week: int = Field(..., description="Start week of the season")
    season_end_week: int = Field(..., description="End week of the season")
    season_start_description: str = Field(...,
                                          description="Description of season start")
    season_end_description: str = Field(...,
                                        description="Description of season end")


class SeasonAnalysisResponse(BaseModel):
    seasons: List[Season]
    monthly_average: MonthlyAverage
    growthRates: GrowthRateResponse


class SpatialFeatureProperties(BaseModel):
    process_id: str
    cell_id: str
    cell_area: float
    cell_intersection_area: float
    cell_coverage_ratio: float
    total_observed_area: float
    total_ndvi_area: float
    ndvi_score: float
    total_whc_area: float
    whc_score: float


class CustomFeatureModel(FeatureModel):
    properties: SpatialFeatureProperties


class SpatialAnalysisResponse(BaseModel):
    type: str = Field(Literal["FeatureCollection"])
    features: List[CustomFeatureModel]


class CustomFeatureModel(FeatureModel):
    properties: SpatialFeatureProperties


class AnalysisRecord(BaseModel):
    observed_areas: List[Dict]
    ndvi_areas: List[Dict]
    whc_areas: List[Dict]
    dateString: str


class AvailableDatesResponse(BaseModel):
    dates: List[datetime] = Field(...,
                                  description="List of available capture dates")
