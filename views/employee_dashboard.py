import customtkinter as ctk
from controllers.appointment_controller import AppointmentController, AppointmentError
from utils.session import Session
from views.base_dashboard import BaseDashboard
from views.notifications_page import NotificationsPage

_STATUS_MAP = {
    'pending':   ("Εκκρεμεί",      ("#e67e22", "#d68910")),
    'confirmed': ("✔ Επιβεβαιωμένο",  ("#27ae60", "#2ecc71")),
    'done':      ("✔ Ολοκληρώθηκε",   ("#27ae60", "#2ecc71")),
    'cancelled': ("✘ Ακυρώθηκε",      ("#e74c3c", "#922b21")),
}

_TIME_SLOTS = [
    f"{h:02d}:{m:02d}"
    for h in range(9, 18)
    for m in (0, 30)
]


class EmployeeDashboard(BaseDashboard):
    NAV_ITEMS = [
        ("Αρχική",       "home"),
        ("Ραντεβού μου", "appointments"),
        ("Ειδοποιήσεις", "notifications"),
    ]

    def _build_pages(self):
        self._register_page("home",          _HomePage(self._content))
        self._register_page("appointments",  _AppointmentsPage(self._content))
        self._register_page("notifications", NotificationsPage(self._content))


#  Appointments — UC 2.3


class _AppointmentsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._sel_appt = None   

        self._build_list_frame()
        self._build_detail_frame()
        self._build_reject_frame()
        self._build_reschedule_frame()

        self._go_list()

    def _hide_all(self):
        for f in (
            self._list_frame, self._detail_frame,
            self._reject_frame, self._reschedule_frame,
        ):
            f.grid_remove()

    def refresh(self):
        self._go_list()

    def _build_list_frame(self):
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.columnconfigure(0, weight=1)
        self._list_frame.rowconfigure(2, weight=1)

        hdr = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 8))
        ctk.CTkLabel(
            hdr, text="📅 Αιτήσεις & Ραντεβού",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        self._list_msg_var = ctk.StringVar()
        self._list_msg_label = ctk.CTkLabel(
            self._list_frame, textvariable=self._list_msg_var,
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self._list_msg_label.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 4))

        self._list_container = ctk.CTkScrollableFrame(self._list_frame, corner_radius=10)
        self._list_container.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        self._list_container.columnconfigure(0, weight=1)

    def _go_list(self):
        self._hide_all()
        self._list_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_list()

    def _refresh_list(self):
        for w in self._list_container.winfo_children():
            w.destroy()

        user  = Session.current_user()
        appts = AppointmentController.get_by_employee(user.id)

        # alt flow 1 — no requests
        if not appts:
            ctk.CTkLabel(
                self._list_container,
                text="Δεν υπάρχουν αιτήσεις ραντεβού.",
                text_color="gray",
            ).grid(row=0, column=0, pady=48)
            return

        for i, appt in enumerate(appts):
            card = ctk.CTkFrame(self._list_container, corner_radius=10)
            card.grid(row=i, column=0, sticky="ew", padx=8, pady=6)
            card.columnconfigure(0, weight=1)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                top,
                text=f" {appt.scheduled_at}  —  {appt.service_name}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")
            status_text, status_color = _STATUS_MAP.get(
                appt.status, (appt.status, ("gray", "gray"))
            )
            ctk.CTkLabel(
                top, text=status_text, text_color=status_color,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

            meta = f"Πελάτης: {appt.customer_name}   |   Διάρκεια: {appt.duration_min} λεπτά   |   Τιμή: {appt.price:.2f} €"
            if appt.notes:
                meta += f"   |   Σημείωση: {appt.notes}"
            ctk.CTkLabel(
                card, text=meta, anchor="w",
                text_color="gray", font=ctk.CTkFont(size=12),
            ).pack(fill="x", padx=16)

            # step 3 — select appointment
            footer = ctk.CTkFrame(card, fg_color="transparent")
            footer.pack(fill="x", padx=16, pady=(6, 12))
            ctk.CTkButton(
                footer, text="Λεπτομέρειες →", width=140, height=28,
                font=ctk.CTkFont(size=11),
                command=lambda a=appt: self._open_detail(a),
            ).pack(side="right")

    #  DETAIL 
    def _build_detail_frame(self):
        self._detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._detail_frame.columnconfigure(0, weight=1)
        self._detail_frame.rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(24, 12))
        hdr.columnconfigure(1, weight=1)
        ctk.CTkButton(
            hdr, text="← Πίσω", width=100,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=self._go_list,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hdr, text="Στοιχεία Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=20)

        body = ctk.CTkFrame(self._detail_frame, corner_radius=12)
        body.grid(row=1, column=0, sticky="n", padx=32, pady=(0, 24))

        self._detail_text = ctk.CTkLabel(
            body, text="", justify="left",
            font=ctk.CTkFont(size=13),
        )
        self._detail_text.pack(padx=40, pady=(28, 20))

        self._detail_status_label = ctk.CTkLabel(
            body, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._detail_status_label.pack(pady=(0, 20))

        self._detail_msg = ctk.StringVar()
        self._detail_msg_label = ctk.CTkLabel(
            body, textvariable=self._detail_msg,
            font=ctk.CTkFont(size=12), wraplength=380,
        )
        self._detail_msg_label.pack(padx=40, pady=(0, 8))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(pady=(0, 32))
        self._accept_btn = ctk.CTkButton(
            btn_row, text="✓ Αποδοχή", width=130,
            fg_color=("#27ae60", "#1e8449"), hover_color=("#229954", "#196f3d"),
            command=self._accept,
        )
        self._accept_btn.pack(side="left", padx=(0, 8))
        self._reject_btn = ctk.CTkButton(
            btn_row, text="✕ Απόρριψη", width=130,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._go_reject,
        )
        self._reject_btn.pack(side="left", padx=(0, 8))
        self._reschedule_btn = ctk.CTkButton(
            btn_row, text="🗓 Αναπρ/σμός", width=150,
            fg_color=("gray60", "gray30"), hover_color=("gray50", "gray40"),
            command=self._go_reschedule,
        )
        self._reschedule_btn.pack(side="left", padx=(0, 8))
        self._complete_btn = ctk.CTkButton(
            btn_row, text="✔ Ολοκλήρωση", width=150,
            fg_color=("#1a5276", "#1f618d"), hover_color=("#154360", "#1a5276"),
            command=self._complete,
        )
        self._complete_btn.pack(side="left")

    def _open_detail(self, appt):
        self._sel_appt = appt
        status_text, status_color = _STATUS_MAP.get(
            appt.status, (appt.status, ("gray", "gray"))
        )
        self._detail_text.configure(
            text=(
                f"Πελάτης:      {appt.customer_name}\n"
                f"Υπηρεσία:    {appt.service_name}\n"
                f"Ημερομηνία: {appt.scheduled_at}\n"
                f"Διάρκεια:    {appt.duration_min} λεπτά\n"
                f"Κόστος:       {appt.price:.2f} €\n"
                + (f"Σημείωση:    {appt.notes}" if appt.notes else "")
            )
        )
        self._detail_status_label.configure(text=f"Κατάσταση: {status_text}", text_color=status_color)
        self._detail_msg.set("")

        # Αποδοχή: μόνο pending | Απόρριψη/Αναπρ: pending ή confirmed
        # Ολοκλήρωση: μόνο confirmed
        self._accept_btn.configure(
            state="normal" if appt.status == "pending" else "disabled"
        )
        self._reject_btn.configure(
            state="normal" if appt.status in ("pending", "confirmed") else "disabled"
        )
        self._reschedule_btn.configure(
            state="normal" if appt.status in ("pending", "confirmed") else "disabled"
        )
        self._complete_btn.configure(
            state="normal" if appt.status == "confirmed" else "disabled"
        )

        self._hide_all()
        self._detail_frame.grid(row=0, column=0, sticky="nsew")

    def _accept(self):
        user = Session.current_user()
        try:
            AppointmentController.accept_appointment(self._sel_appt.id, user.id)
            self._list_msg_label.configure(text_color=("#27ae60", "#2ecc71"))
            self._list_msg_var.set(
                f"✔ Το ραντεβού #{self._sel_appt.id} αποδεκτό. Ο πελάτης ενημερώθηκε."
            )
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            self._detail_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._detail_msg.set(str(e))

    def _complete(self):
        user = Session.current_user()
        try:
            AppointmentController.complete_appointment(self._sel_appt.id, user.id)
            self._list_msg_label.configure(text_color=("#1a5276", "#1f618d"))
            self._list_msg_var.set(
                f"✔ Το ραντεβού #{self._sel_appt.id} ολοκληρώθηκε. "
                f"Ο πελάτης ενημερώθηκε και μπορεί να αξιολογήσει."
            )
            self.after(6000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            self._detail_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._detail_msg.set(str(e))

    # REJECT 
    def _build_reject_frame(self):
        self._reject_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._reject_frame.columnconfigure(0, weight=1)
        self._reject_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._reject_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="✕  Απόρριψη Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 8))
        ctk.CTkLabel(
            card,
            text="Παρακαλώ αναφέρετε τον λόγο απόρριψης (προαιρετικά):",
            text_color="gray",
        ).pack(padx=52, pady=(0, 8))

        self._reject_reason = ctk.CTkEntry(
            card, width=360,
            placeholder_text="π.χ. αναρρωτική άδεια, έκτακτη ανάγκη…",
        )
        self._reject_reason.pack(padx=52, pady=(0, 8))

        self._reject_msg = ctk.StringVar()
        self._reject_msg_label = ctk.CTkLabel(
            card, textvariable=self._reject_msg,
            font=ctk.CTkFont(size=12), wraplength=360,
        )
        self._reject_msg_label.pack(padx=52, pady=(0, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="← Ακύρωση", width=130,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._open_detail(self._sel_appt),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="Επιβεβαίωση Απόρριψης", width=210,
            fg_color=("#e74c3c", "#922b21"), hover_color=("#c0392b", "#7b241c"),
            command=self._confirm_reject,
        ).pack(side="left")

    def _go_reject(self):
        self._reject_reason.delete(0, "end")
        self._reject_msg.set("")
        self._hide_all()
        self._reject_frame.grid(row=0, column=0, sticky="nsew")

    def _confirm_reject(self):
        user   = Session.current_user()
        reason = self._reject_reason.get().strip()
        try:
            AppointmentController.reject_appointment(self._sel_appt.id, user.id, reason)
            self._list_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._list_msg_var.set(
                f"✕ Το ραντεβού #{self._sel_appt.id} απορρίφθηκε. Ο πελάτης ενημερώθηκε."
            )
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            self._reject_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._reject_msg.set(str(e))

    # RESCHEDULE 
    def _build_reschedule_frame(self):
        self._reschedule_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._reschedule_frame.columnconfigure(0, weight=1)
        self._reschedule_frame.rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self._reschedule_frame, corner_radius=16)
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text=" Αναπρογραμματισμός Ραντεβού",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=52, pady=(36, 16))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=52)

        ctk.CTkLabel(form, text="Νέα ημερομηνία (ΕΕΕΕ-ΜΜ-ΗΗ):", anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self._resched_date = ctk.CTkEntry(
            form, width=220, placeholder_text="π.χ. 2026-06-15"
        )
        self._resched_date.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(form, text="Νέα ώρα:", anchor="w").grid(
            row=2, column=0, sticky="w", pady=(0, 4)
        )
        self._resched_time = ctk.CTkComboBox(
            form, values=_TIME_SLOTS, width=220, state="readonly"
        )
        self._resched_time.set(_TIME_SLOTS[0])
        self._resched_time.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self._resched_msg = ctk.StringVar()
        self._resched_msg_label = ctk.CTkLabel(
            card, textvariable=self._resched_msg,
            font=ctk.CTkFont(size=12), wraplength=360,
        )
        self._resched_msg_label.pack(padx=52, pady=(4, 8))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 36))
        ctk.CTkButton(
            btn_row, text="← Πίσω", width=110,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
            command=lambda: self._open_detail(self._sel_appt),
        ).pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            btn_row, text="✓ Αποστολή Πρότασης", width=200,
            command=self._confirm_reschedule,
        ).pack(side="left")

    def _go_reschedule(self):
        self._resched_date.delete(0, "end")
        self._resched_time.set(_TIME_SLOTS[0])
        self._resched_msg.set("")
        self._hide_all()
        self._reschedule_frame.grid(row=0, column=0, sticky="nsew")

    def _confirm_reschedule(self):
        date_str = self._resched_date.get().strip()
        time_str = self._resched_time.get()
        new_iso  = f"{date_str} {time_str}"
        user     = Session.current_user()
        try:
            AppointmentController.reschedule_appointment(self._sel_appt.id, user.id, new_iso)
            self._list_msg_label.configure(text_color=("#e67e22", "#d68910"))
            self._list_msg_var.set(
                f" Πρόταση αναπρογραμματισμού #{self._sel_appt.id} απεστάλη στον πελάτη."
            )
            self.after(5000, lambda: self._list_msg_var.set(""))
            self._go_list()
        except AppointmentError as e:
            self._resched_msg_label.configure(text_color=("#e74c3c", "#e74c3c"))
            self._resched_msg.set(str(e))


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

