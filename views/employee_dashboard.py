import customtkinter as ctk
from utils.session import Session
from views.base_dashboard import BaseDashboard
from views.notifications_page import NotificationsPage


class EmployeeDashboard(BaseDashboard):
    NAV_ITEMS = [
        ("Αρχική",       "home"),
        ("Ραντεβού μου", "appointments"),
        ("Ειδοποιήσεις", "notifications"),
    ]

    def _build_pages(self):
        self._register_page("home",          _HomePage(self._content))
        self._register_page("appointments",  _PlaceholderPage(self._content, "Ραντεβού μου"))
        self._register_page("notifications", NotificationsPage(self._content))

class _HomePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        user = Session.current_user()
        box = ctk.CTkFrame(self, corner_radius=16)
        box.grid(row=0, column=0)
        ctk.CTkLabel(box, text="💇", font=ctk.CTkFont(size=52)).pack(pady=(32, 8))
        ctk.CTkLabel(
            box, text="Καλωσήρθατε, " + user.first_name,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=40)
        ctk.CTkLabel(
            box,
            text="Χρησιμοποιήστε το μενού αριστερά\nγια να δείτε τα ραντεβού σας.",
            text_color="gray",
            justify="center",
        ).pack(pady=(8, 32), padx=40)


class _PlaceholderPage(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=f"{title}\n\nΈρχεται σύντομα…",
            font=ctk.CTkFont(size=18),
            text_color="gray",
            justify="center",
        ).grid(row=0, column=0)
