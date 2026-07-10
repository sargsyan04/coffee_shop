from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    CUSTOMER = "customer"
    BARISTA = "barista"
    ADMIN = "admin"