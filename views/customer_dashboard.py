import customtkinter as ctk
from views.base_dashboard import BaseDashboard
from views.notifications_page import NotificationsPage

class CustomerDashboard(BaseDashboard):
    NAV_ITEMS = [
        ("Αρχική",           "home"),
        ("Κομμωτήρια",       "salons"),
        ("E-Shop",            "eshop"),
        ("Καλάθι",           "cart"),
        ("Παραγγελίες μου",  "orders"),
        ("Ραντεβού",         "appointments"),
        ("Ειδοποιήσεις",     "notifications"),
    ]

    def _build_pages(self):
        nav = self._show_page
        self._register_page("home",          _HomePage(self._content))
        self._register_page("salons",        _PlaceholderPage(self._content, "Κομμωτήρια"))
        self._register_page("eshop",         _PlaceholderPage(self._content, "E-Shop"))
        self._register_page("cart",          _PlaceholderPage(self._content, "Καλάθι"))
        self._register_page("orders",        _PlaceholderPage(self._content, "Παραγγελίες μου"))
        self._register_page("appointments",  _PlaceholderPage(self._content, "Ραντεβού"))
        self._register_page("notifications", NotificationsPage(self._content))

class _HomePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        box = ctk.CTkFrame(self, corner_radius=16)
        box.grid(row=0, column=0)
        ctk.CTkLabel(box, text="✨", font=ctk.CTkFont(size=52)).pack(pady=(32, 8))
        ctk.CTkLabel(
            box, text="Καλωσήρθατε στο BeautyHub!",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=40)
        ctk.CTkLabel(
            box,
            text="Ψωνίστε από το E-Shop, κλείστε ραντεβού\nκαι δείτε το ιστορικό παραγγελιών σας.",
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
