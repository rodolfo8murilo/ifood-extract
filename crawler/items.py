# pylint: disable=too-few-public-methods
from typing import Optional
from pydantic import BaseModel, Field


class IFoodItemModel(BaseModel):
    title: str = Field(..., description="Title or name of the product")
    url: str = Field(..., description="URL of the product page")
    image: Optional[str] = Field(None, description="URL of the product image")
    normal_price: Optional[str] = Field(
        None, description="Original/normal price of the product as a string"
    )
    discount_price: Optional[str] = Field(
        None, description="Discounted price as a string"
    )
    status: str = Field(
        default="success", description="Status of the request/collection"
    )
    error: Optional[str] = Field(
        None, description="Error message as a string, in case of failure"
    )
