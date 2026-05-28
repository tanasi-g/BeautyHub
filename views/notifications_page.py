"""
Κοινή σελίδα ειδοποιήσεων.
Χρησιμοποιείται και στα τρία dashboards (admin, employee, customer).
"""
from __future__ import annotations
import customtkinter as ctk
from controllers.notification_controller import NotificationController
from controllers.appointment_controller import AppointmentController, AppointmentError
from utils.session import Session


class NotificationsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_header()
        self._build_list()

    # ---------------------------------------------------------------- build
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 0))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Ειδοποιήσεις",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._mark_all_btn = ctk.CTkButton(
            hdr,
            text="Σήμανση όλων ως αναγνωσμένα",
            width=280, height=34,
            command=self._mark_all_read,
        )
        self._mark_all_btn.grid(row=0, column=1, sticky="e")

        self._msg_var = ctk.StringVar()
        ctk.CTkLabel(
            hdr,
            textvariable=self._msg_var,
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _build_list(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=32, pady=16)
        self._scroll.columnconfigure(0, weight=1)

    # ---------------------------------------------------------------- refresh
    def refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._msg_var.set("")

        user = Session.current_user()
        if not user:
            return

        notifs = NotificationController.get_for_user(user.id)
        unread  = [n for n in notifs if not n.is_read]

        self._mark_all_btn.configure(
            state="normal" if unread else "disabled"
        )

        if not notifs:
            ctk.CTkLabel(
                self._scroll,
                text="Δεν υπάρχουν ειδοποιήσεις.",
                text_color="gray",
                font=ctk.CTkFont(size=14),
            ).grid(row=0, column=0, pady=60)
            return

        for i, notif in enumerate(notifs):
            self._render_card(i, notif)

    # ---------------------------------------------------------------- card
    def _render_card(self, row: int, notif):
        is_unread = not notif.is_read

        card = ctk.CTkFrame(
            self._scroll,
            corner_radius=10,
            fg_color=("gray86", "gray22") if is_unread else ("gray92", "gray15"),
            border_width=2 if is_unread else 0,
            border_color=("#3498db", "#2980b9"),
        )
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        card.columnconfigure(0, weight=1)

        # ── top row: blue dot + message text ──────────────────────────
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))

        if is_unread:
            ctk.CTkLabel(
                top,
                text="●",
                text_color=("#3498db", "#5dade2"),
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            top,
            text=notif.message,
            wraplength=660,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold" if is_unread else "normal"),
        ).pack(side="left", fill="x", expand=True)

        # ── bottom row: timestamp + mark-read button ──────────────────
        bot = ctk.CTkFrame(card, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            bot,
            text=notif.created_at,
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).pack(side="left")

        if is_unread:
            ctk.CTkButton(
                bot,
                text="✓  Σήμανση ως αναγνωσμένο",
                width=230, height=26,
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray80", "gray30"),
                command=lambda nid=notif.id: self._mark_one(nid),
            ).pack(side="right")

        # ── action row: αποδοχή / απόρριψη πρότασης αλλαγής ραντεβού ──
        if notif.type == "reschedule_proposal" and notif.appointment_id:
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=16, pady=(0, 12))
            ctk.CTkButton(
                actions,
                text="✓  Αποδοχή",
                width=140, height=30,
                fg_color=("#27ae60", "#1e8449"),
                hover_color=("#229954", "#196f3d"),
                command=lambda aid=notif.appointment_id, nid=notif.id:
                    self._accept_reschedule(aid, nid),
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                actions,
                text="✕  Απόρριψη",
                width=140, height=30,
                fg_color=("#e74c3c", "#922b21"),
                hover_color=("#c0392b", "#7b241c"),
                command=lambda aid=notif.appointment_id, nid=notif.id:
                    self._reject_reschedule(aid, nid),
            ).pack(side="left")

    # ---------------------------------------------------------------- actions
    def _mark_one(self, notif_id: int):
        NotificationController.mark_read(notif_id)
        self.refresh()

    def _mark_all_read(self):
        user = Session.current_user()
        if not user:
            return
        NotificationController.mark_all_read(user.id)
        self._msg_var.set("Όλες οι ειδοποιήσεις σημάνθηκαν ως αναγνωσμένες.")
        self.refresh()

    def _accept_reschedule(self, appt_id: int, notif_id: int):
        user = Session.current_user()
        if not user:
            return
        try:
            AppointmentController.customer_accept_reschedule(appt_id, user.id)
            NotificationController.mark_read(notif_id)
            self._msg_var.set("Η νέα ώρα του ραντεβού επιβεβαιώθηκε.")
        except AppointmentError as e:
            self._msg_var.set(str(e))
        self.refresh()

    def _reject_reschedule(self, appt_id: int, notif_id: int):
        user = Session.current_user()
        if not user:
            return
        try:
            AppointmentController.customer_reject_reschedule(appt_id, user.id)
            NotificationController.mark_read(notif_id)
            self._msg_var.set("Η αλλαγή του ραντεβού απορρίφθηκε.")
        except AppointmentError as e:
            self._msg_var.set(str(e))
        self.refresh()
