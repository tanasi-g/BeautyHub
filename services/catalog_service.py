
from models.service import Service
from repositories.service_repository import ServiceRepository
from services.errors import ServiceError


class CatalogService:

    @staticmethod
    def count() -> int:
        return ServiceRepository.count()

    @staticmethod
    def get_all() -> list[Service]:
        return ServiceRepository.get_all()

    @staticmethod
    def create(name: str, description: str, duration_min: str, price: str) -> Service:
        name        = name.strip()
        description = description.strip() or None

        if not name:
            raise ServiceError("Το όνομα υπηρεσίας είναι υποχρεωτικό.")

        try:
            dur = int(duration_min)
        except ValueError:
            raise ServiceError("Η διάρκεια πρέπει να είναι ακέραιος αριθμός.")
        if dur <= 0:
            raise ServiceError("Η διάρκεια πρέπει να είναι θετικός αριθμός.")

        try:
            prc = float(price.replace(",", "."))
        except ValueError:
            raise ServiceError("Η τιμή πρέπει να είναι αριθμός.")
        if prc < 0:
            raise ServiceError("Η τιμή δεν μπορεί να είναι αρνητική.")

        service_id = ServiceRepository.create(name, description, dur, prc)
        return Service(
            id=service_id,
            name=name,
            description=description,
            duration_min=dur,
            price=prc,
            is_active=True,
        )
