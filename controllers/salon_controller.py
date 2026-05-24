from models.salon import Salon
from models.service import Service
from services.salon_service import SalonService
from services.errors import SalonError  # re-exported για τα views

__all__ = ["SalonController", "SalonError"]


class SalonController:

    @staticmethod
    def count() -> int:
        return SalonService.count()

    @staticmethod
    def get_all() -> list[Salon]:
        return SalonService.get_all()

    @staticmethod
    def search(keyword: str, service_id: int | None = None) -> list[Salon]:
        return SalonService.search(keyword, service_id)

    @staticmethod
    def create(name: str, address: str, city: str, phone: str, email: str) -> Salon:
        return SalonService.create(name, address, city, phone, email)

    @staticmethod
    def toggle_active(salon_id: int) -> bool:
        return SalonService.toggle_active(salon_id)

    @staticmethod
    def get_services(salon_id: int) -> list[Service]:
        return SalonService.get_services(salon_id)

    @staticmethod
    def get_available_services(salon_id: int) -> list[Service]:
        return SalonService.get_available_services(salon_id)

    @staticmethod
    def add_service(salon_id: int, service_id: int) -> None:
        SalonService.add_service(salon_id, service_id)

    @staticmethod
    def remove_service(salon_id: int, service_id: int) -> None:
        SalonService.remove_service(salon_id, service_id)
