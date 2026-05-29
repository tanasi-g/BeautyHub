import customtkinter as ctk
from PIL import Image

from controllers.auth_controller import AuthController, AuthError
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


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color=_BG)
        self._on_login_success = on_login_success
        self._show_register = False
        self._build_ui()

    # ------------------------------------------------------------------ build
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Outer card with soft shadow simulation via a slightly darker frame
        shadow = ctk.CTkFrame(self, fg_color=_MUTED, corner_radius=20)
        shadow.grid(row=0, column=0)
        shadow.pack_propagate(False)
        shadow.configure(width=378, height=506)

        self._card = ctk.CTkFrame(shadow, fg_color=_CARD_BG, corner_radius=18, width=370, height=498)
        self._card.place(relx=0.5, rely=0.5, anchor="center")
        self._card.pack_propagate(False)

        # Logo
        logo = ctk.CTkImage(
            light_image=Image.open("resources/logo.jpeg"),
            dark_image=Image.open("resources/logo.jpeg"),
            size=(120, 64),
        )
        ctk.CTkLabel(self._card, image=logo, text="").pack(pady=(28, 0))

        # Title + decorative separator
        ctk.CTkLabel(
            self._card,
            text="Καλωσήρθατε",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=_TEXT,
        ).pack(pady=(8, 0))


        # Pink divider
        sep = ctk.CTkFrame(self._card, fg_color=_MUTED, height=2, corner_radius=1)
        sep.pack(fill="x", padx=30, pady=(0, 12))

        # Form area
        self._form_frame = ctk.CTkFrame(self._card, fg_color="transparent")
        self._form_frame.pack(fill="x", padx=24)

        # Error label
        self._error_var = ctk.StringVar()
        ctk.CTkLabel(
            self._card,
            textvariable=self._error_var,
            text_color=_ERROR,
            font=ctk.CTkFont(size=11),
            wraplength=320,
        ).pack(pady=(4, 0))

        # Toggle link
        self._toggle_btn = ctk.CTkButton(
            self._card,
            text="Δεν έχετε λογαριασμό; Εγγραφή →",
            fg_color="transparent",
            hover_color="#fff0f3",
            text_color=_ACCENT,
            font=ctk.CTkFont(size=11, underline=True),
            command=self._toggle_mode,
        )
        self._toggle_btn.pack(pady=(6, 16))

        self._build_login_form()

    def _clear_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

    def _label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text, anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=_SUBTEXT,
        ).pack(fill="x")

    def _entry(self, parent, placeholder, secret=False, height=38):
        e = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            show="•" if secret else "",
            height=height,
            fg_color=_ENTRY_BG,
            border_color=_BORDER,
            border_width=1,
            text_color=_TEXT,
            placeholder_text_color=_MUTED,
            corner_radius=10,
        )
        e.pack(fill="x", pady=(2, 10))
        return e

    #  login
    def _build_login_form(self):
        self._clear_form()
        self._card.master.configure(height=506)
        self._card.configure(height=498)
        self._show_register = False

        self._label(self._form_frame, "ΟΝΟΜΑ ΧΡΗΣΤΗ")
        self._username_entry = self._entry(self._form_frame, "π.χ. maria_k")

        self._label(self._form_frame, "ΚΩΔΙΚΟΣ ΠΡΟΣΒΑΣΗΣ")
        self._password_entry = self._entry(self._form_frame, "••••••••", secret=True)

        # Eye button inside password entry
        self._eye_btn = ctk.CTkButton(
            self._password_entry,
            text="👁", width=30, height=26,
            fg_color="transparent",
            hover_color=_BG,
            text_color=_SUBTEXT,
            font=ctk.CTkFont(size=14),
            command=self._toggle_password,
        )
        self._eye_btn.place(relx=1.0, rely=0.5, anchor="e", x=-4)

        self._username_entry.bind("<Return>", lambda _: self._password_entry.focus())
        self._password_entry.bind("<Return>", lambda _: self._do_login())

        ctk.CTkButton(
            self._form_frame,
            text="Σύνδεση  →",
            height=42,
            fg_color=_ACCENT,
            hover_color=_ACCENT_HV,
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=12,
            command=self._do_login,
        ).pack(fill="x", pady=(4, 0))

    #  register
    def _build_register_form(self):
        self._clear_form()
        self._card.master.configure(height=590)
        self._card.configure(height=582)
        self._show_register = True

        scroll = ctk.CTkScrollableFrame(
            self._form_frame, fg_color="transparent", height=310
        )
        scroll.pack(fill="x")

        fields = [
            ("ΟΝΟΜΑ ΧΡΗΣΤΗ *",       "_reg_username", False, "π.χ. maria_k"),
            ("EMAIL *",               "_reg_email",    False, "email@example.com"),
            ("ΟΝΟΜΑ *",               "_reg_first",    False, "Μαρία"),
            ("ΕΠΩΝΥΜΟ *",             "_reg_last",     False, "Κατσαρού"),
            ("ΤΗΛΕΦΩΝΟ",              "_reg_phone",    False, "6900000000"),
            ("ΚΩΔΙΚΟΣ *",             "_reg_pw",       True,  "••••••••"),
            ("ΕΠΙΒΕΒΑΙΩΣΗ ΚΩΔΙΚΟΥ *", "_reg_pw2",      True,  "••••••••"),
        ]
        for label, attr, secret, ph in fields:
            self._label(scroll, label)
            entry = self._entry(scroll, ph, secret=secret, height=32)
            # re-pack with smaller bottom padding for compact register form
            entry.pack_forget()
            entry = ctk.CTkEntry(
                scroll,
                placeholder_text=ph,
                show="•" if secret else "",
                height=32,
                fg_color=_ENTRY_BG,
                border_color=_BORDER,
                border_width=1,
                text_color=_TEXT,
                placeholder_text_color=_MUTED,
                corner_radius=10,
            )
            entry.pack(fill="x", pady=(2, 6))
            setattr(self, attr, entry)

        ctk.CTkButton(
            scroll,
            text="Εγγραφή  →",
            height=38,
            fg_color=_ACCENT,
            hover_color=_ACCENT_HV,
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=12,
            command=self._do_register,
        ).pack(fill="x", pady=(8, 0))

    #  actions
    def _toggle_mode(self):
        self._error_var.set("")
        if self._show_register:
            self._build_login_form()
            self._toggle_btn.configure(text="Δεν έχετε λογαριασμό; Εγγραφή →")
        else:
            self._build_register_form()
            self._toggle_btn.configure(text="Έχετε ήδη λογαριασμό; Σύνδεση →")

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
