import customtkinter as ctk
from database.connection import Database
from database.seed import seed_database
from models.user import User
from views.login_view import LoginView


class App(ctk.CTk):
    WIDTH  = 1100
    HEIGHT = 680

    def __init__(self):
        super().__init__()
        self.title("Beauty Hub – Σύστημα Διαχείρισης")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(900, 600)
        self._current_view: ctk.CTkFrame | None = None
        self._show_login()

    def _show_login(self):
        self._swap(LoginView(self, on_login_success=self._on_login))

    def _on_login(self, user: User):
        from views.admin_dashboard    import AdminDashboard
        from views.employee_dashboard import EmployeeDashboard
        from views.customer_dashboard import CustomerDashboard

        dashboard_cls = {
            "admin":    AdminDashboard,
            "employee": EmployeeDashboard,
            "customer": CustomerDashboard,
        }.get(user.role_name, CustomerDashboard)

        self._swap(dashboard_cls(self, on_logout=self._show_login))

    def _swap(self, new_view: ctk.CTkFrame):
        if self._current_view:
            self._current_view.destroy()
        self._current_view = new_view
        new_view.pack(fill="both", expand=True)


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    Database.initialize()
    seed_database()

    app = App()
    app.mainloop()

    Database.close()


if __name__ == "__main__":
    main()
