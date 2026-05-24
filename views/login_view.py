import customtkinter as ctk
from PIL import Image

from controllers.auth_controller import AuthController, AuthError
from utils.session import Session


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="transparent")
        self._on_login_success = on_login_success
        self._show_register = False
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._card = ctk.CTkFrame(self, corner_radius=16)
        self._card.grid(row=0, column=0)
        self._card.pack_propagate(False)
        self._card.configure(width=350, height=490)

        logo = ctk.CTkImage(
            light_image=Image.open("resources/logo.jpeg"),
            dark_image=Image.open("resources/logo.jpeg"),
            size=(150, 80),
        )
        ctk.CTkLabel(self._card, image=logo, text="").pack(pady=(36, 0))
        ctk.CTkLabel(
            self._card, text="Σύστημα Διαχείρισης",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(pady=(0, 20))

        # _form_frame δεν καταστρέφεται ποτέ — μόνο τα παιδιά του
        self._form_frame = ctk.CTkFrame(self._card, fg_color="transparent")
        self._form_frame.pack(fill="x", padx=16)

        # error label
        self._error_var = ctk.StringVar()
        ctk.CTkLabel(
            self._card,
            textvariable=self._error_var,
            text_color="#e74c3c",
            font=ctk.CTkFont(size=12),
            wraplength=320,
        ).pack(pady=(6, 0))

        # toggle link
        self._toggle_btn = ctk.CTkButton(
            self._card,
            text="Δεν έχετε λογαριασμό; Εγγραφή",
            fg_color="transparent",
            hover_color=("gray90", "gray20"),
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=12, underline=True),
            command=self._toggle_mode,
        )
        self._toggle_btn.pack(pady=(8, 24))

        self._build_login_form()

    def _clear_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ login
    def _build_login_form(self):
        self._clear_form()
        self._card.configure(height=490)
        self._show_register = False

        ctk.CTkLabel(self._form_frame, text="Όνομα χρήστη", anchor="w").pack(fill="x")
        self._username_entry = ctk.CTkEntry(
            self._form_frame, placeholder_text="π.χ. maria_k", height=38
        )
        self._username_entry.pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(self._form_frame, text="Κωδικός πρόσβασης", anchor="w").pack(fill="x")
        self._password_entry = ctk.CTkEntry(
            self._form_frame, placeholder_text="••••••••", show="•", height=38
        )
        self._password_entry.pack(fill="x", pady=(2, 20))

        # eye button μέσα στο entry με place()
        self._eye_btn = ctk.CTkButton(
            self._password_entry,
            text="👁", width=32, height=28,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=15),
            command=self._toggle_password,
        )
        self._eye_btn.place(relx=1.0, rely=0.5, anchor="e", x=-4)

        self._username_entry.bind("<Return>", lambda _: self._password_entry.focus())
        self._password_entry.bind("<Return>", lambda _: self._do_login())

        ctk.CTkButton(
            self._form_frame, text="Σύνδεση", height=40,
            command=self._do_login,
        ).pack(fill="x")

    # ---------------------------------------------------------------- register
    def _build_register_form(self):
        self._clear_form()
        self._card.configure(height=570)
        self._show_register = True

        # scrollable area μέσα στο σταθερό _form_frame
        scroll = ctk.CTkScrollableFrame(
            self._form_frame, fg_color="transparent", height=310
        )
        scroll.pack(fill="x")

        fields = [
            ("Όνομα χρήστη *",       "_reg_username", False, "π.χ. maria_k"),
            ("Email *",               "_reg_email",    False, "email@example.com"),
            ("Όνομα *",               "_reg_first",    False, "Μαρία"),
            ("Επώνυμο *",             "_reg_last",     False, "Κατσαρού"),
            ("Τηλέφωνο",              "_reg_phone",    False, "6900000000"),
            ("Κωδικός *",             "_reg_pw",       True,  "••••••••"),
            ("Επιβεβαίωση κωδικού *", "_reg_pw2",      True,  "••••••••"),
        ]
        for label, attr, secret, ph in fields:
            ctk.CTkLabel(
                scroll, text=label, anchor="w",
                font=ctk.CTkFont(size=11),
            ).pack(fill="x")
            entry = ctk.CTkEntry(
                scroll,
                placeholder_text=ph,
                show="•" if secret else "",
                height=32,
            )
            entry.pack(fill="x", pady=(2, 6))
            setattr(self, attr, entry)

        ctk.CTkButton(
            scroll, text="Εγγραφή", height=38,
            command=self._do_register,
        ).pack(fill="x", pady=(6, 0))

    # ---------------------------------------------------------------- actions
    def _toggle_mode(self):
        self._error_var.set("")
        if self._show_register:
            self._build_login_form()
            self._toggle_btn.configure(text="Δεν έχετε λογαριασμό; Εγγραφή")
        else:
            self._build_register_form()
            self._toggle_btn.configure(text="Έχετε ήδη λογαριασμό; Σύνδεση")

    def _toggle_password(self):
        current = self._password_entry.cget("show")
        self._password_entry.configure(show="" if current else "•")

    def _do_login(self):
        self._error_var.set("")
        try:
            user = AuthController.login(
                self._username_entry.get(),
                self._password_entry.get(),
            )
            Session.login(user)
            self._on_login_success(user)
        except AuthError as e:
            self._error_var.set(str(e))

    def _do_register(self):
        self._error_var.set("")
        pw  = self._reg_pw.get()
        pw2 = self._reg_pw2.get()
        if pw != pw2:
            self._error_var.set("Οι κωδικοί δεν ταιριάζουν.")
            return
        try:
            user = AuthController.register_customer(
                username=self._reg_username.get(),
                email=self._reg_email.get(),
                password=pw,
                first_name=self._reg_first.get(),
                last_name=self._reg_last.get(),
                phone=self._reg_phone.get(),
            )
            Session.login(user)
            self._on_login_success(user)
        except AuthError as e:
            self._error_var.set(str(e))
