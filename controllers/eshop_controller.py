from models.product import Product
from services.eshop_service import EShopService
from services.errors import EShopError  # re-exported για τα views

__all__ = ["EShopController", "EShopError"]


class EShopController:

    @staticmethod
    def count() -> int:
        return EShopService.count()

    @staticmethod
    def get_all() -> list[Product]:
        return EShopService.get_all()

    @staticmethod
    def search(keyword: str) -> list[Product]:
        return EShopService.search(keyword)

    @staticmethod
    def upload_image(src_path: str) -> str:
        return EShopService.upload_image(src_path)

    @staticmethod
    def create(
        name: str,
        description: str,
        price: str,
        stock: str,
        image_path: str | None,
    ) -> Product:
        return EShopService.create(name, description, price, stock, image_path)
