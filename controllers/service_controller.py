from models.service import Service
from services.catalog_service import CatalogService
from services.errors import ServiceError 

__all__ = ["ServiceController", "ServiceError"]


class ServiceController:

    @staticmethod
    def count() -> int:
        return CatalogService.count()

    @staticmethod
    def get_all() -> list[Service]:
        return CatalogService.get_all()

    @staticmethod
    def create(name: str, description: str, duration_min: str, price: str) -> Service:
        return CatalogService.create(name, description, duration_min, price)
