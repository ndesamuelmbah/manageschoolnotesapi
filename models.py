from typing import List, Optional
from pydantic import BaseModel


class RestaurantMenuItem(BaseModel):
    itemId: int
    itemPrice: float
    itemName: str
    quantity: int
    deliveryPrice: Optional[float] = None
    itemImageUrl: str
    itemDescription: str
    itemDietaryDetails: str
    totalPrice: Optional[float] = None

class OrderedMenuItems(BaseModel):
    items: List[RestaurantMenuItem]