
from __future__ import annotations
import customtkinter as ctk
from utils.session import Session

_BG        = "#e9eff4"
_CARD_BG   = "#f4f7f9"
_ACCENT    = "#4a6984"
_ACCENT_HV = "#1d2d44"
_MUTED     = "#cbd9e0"
_TEXT      = "#2b211a"
_SUBTEXT   = "#5c534c"
_ENTRY_BG  = "#ffffff"
_BORDER    = "#dbe3e8"
_ERROR     = "#c0392b"
_SUCCESS   = "#27ae60"
_WARNING   = "#e67e22"

class BaseDashboard(ctk.CTkFrame):
    SIDEBAR_WIDTH = 235
    NAV_ITEMS: list[tuple[str, str]] = []  

    def __init__(self, master, on_logout):
        super().__init__(master, fg_color=_BG)
        self._on_logout = on_logout
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._active_page: str | None = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._build_pages()

        if self.NAV_ITEMS:
            self._show_page(self.NAV_ITEMS[0][1])

    #  sidebar
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=self.SIDEBAR_WIDTH, corner_radius=0, fg_color=_CARD_BG,border_width=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.rowconfigure(99, weight=1)   

        user = Session.current_user()
  # salon name
        ctk.CTkLabel(
            sidebar, text="BeautyHub",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=_ACCENT,
        ).grid(row=0, column=0, pady=(24, 4), padx=16, sticky="w")

        ctk.CTkFrame(sidebar, height=2, fg_color=_MUTED).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 16)
        )

        # user card
        user_card = ctk.CTkFrame(sidebar, fg_color=_BG, corner_radius=8,
                                 border_width=1, border_color=_BORDER)
        user_card.grid(row=2, column=0, padx=12, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(
            user_card,
            text=user.full_name if user else "—",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=_TEXT,
            wraplength=130,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            user_card,
            text=user.role_display if user else "",
            font=ctk.CTkFont(size=11),
            text_color=_SUBTEXT,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 10))

        # nav buttons
        for idx, (label, key) in enumerate(self.NAV_ITEMS, start=3):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color=_MUTED,
                text_color=_TEXT,
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self._show_page(k),
            )
            btn.grid(row=idx, column=0, padx=12, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

      # logout
        ctk.CTkButton(
            sidebar,
            text="⏻  Αποσύνδεση",
            anchor="w",
            height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#fdecea",
            text_color=_ERROR,
            font=ctk.CTkFont(size=13),
            command=self._do_logout,
        ).grid(row=100, column=0, padx=12, pady=(0, 20), sticky="ew")

    def _build_content_area(self):
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=_BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)


    #  pages
    def _build_pages(self):
        """Υποκλάσεις υλοποιούν αυτή τη μέθοδο και καλούν _register_page()."""

    def _register_page(self, key: str, frame: ctk.CTkFrame):
        frame.grid(row=0, column=0, sticky="nsew", in_=self._content)
        frame.grid_remove()
        self._pages[key] = frame

    def _show_page(self, key: str):
        if self._active_page:
            self._pages[self._active_page].grid_remove()
            btn = self._nav_buttons.get(self._active_page)
            if btn:
                btn.configure(fg_color="transparent", text_color=_TEXT)

        page = self._pages[key]
        page.grid()
        self._active_page = key

        btn = self._nav_buttons.get(key)
        if btn:
            btn.configure(fg_color=_ACCENT,text_color="#ffffff")

        # ανανέωση δεδομένων κάθε φορά που εμφανίζεται η σελίδα
        if hasattr(page, "refresh"):
            page.refresh()

        # ενημέρωση badge αδιάβαστων ειδοποιήσεων στο sidebar
        self._update_notif_badge()

    def _update_notif_badge(self) -> None:
        """Ενημερώνει τον αριθμό αδιάβαστων ειδοποιήσεων στο κουμπί πλοήγησης."""
        btn = self._nav_buttons.get("notifications")
        if not btn:
            return
        user = Session.current_user()
        if not user:
            return
        try:
            from controllers.notification_controller import NotificationController
            count = NotificationController.count_unread(user.id)
        except Exception:
            return
        base_label = next(
            (lbl for lbl, k in self.NAV_ITEMS if k == "notifications"),
            "  Ειδοποιήσεις",
        )
        btn.configure(
            text=f"{base_label}  ({count})" if count > 0 else base_label
        )

    #  logout
    def _do_logout(self):
        Session.logout()
        self._on_logout()
