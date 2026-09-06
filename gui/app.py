"""tkinter メインウィンドウ"""

import os
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, set_language, t
from core import config
from core.app_info import SUPPORT_LINKS, VERSION
from core.file_reader import Chapter, load_chapters, split_chapters_by_chars
from core.providers import all_providers, get_provider
from core.providers.base import CancelledError, ProviderError
from core.tts_engine import (
    extract_preview_text,
    generate_chapters,
    get_language_codes,
    voices_for_locale,
)


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, provider, on_saved=None):
        super().__init__(master)
        self.provider = provider
        self.on_saved = on_saved
        self.title(t("provider.settings_title", provider=provider.label))
        self.resizable(False, False)
        self.grab_set()

        fields = {**provider.requires_credentials(), **provider.optional_credentials()}
        saved = config.get_provider_credentials(provider.name)

        self.vars: dict[str, tk.StringVar] = {}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=10)
        for index, (field, desc) in enumerate(fields.items()):
            label_row = index * 2
            entry_row = label_row + 1
            ttk.Label(frm, text=desc).grid(
                row=label_row, column=0, columnspan=2, sticky="w", pady=(3, 1)
            )
            var = tk.StringVar(value=saved.get(field, ""))
            self.vars[field] = var
            entry = ttk.Entry(frm, textvariable=var, width=48)
            if field == "api_key":
                entry.config(show="*")
            entry.grid(row=entry_row, column=0, sticky="we", pady=(0, 8))
            if "path" in field or "json" in field or "file" in field:
                ttk.Button(
                    frm,
                    text=t("browse"),
                    command=lambda v=var: self._browse(v),
                ).grid(row=entry_row, column=1, padx=(4, 0), pady=(0, 8))
        frm.columnconfigure(0, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            btns,
            text=t("provider.credentials_note"),
            foreground="#888",
        ).pack(side="left")
        ttk.Button(btns, text=t("button.save"), command=self._save).pack(side="right", padx=4)
        ttk.Button(btns, text=t("button.cancel"), command=self.destroy).pack(side="right")

    def _browse(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), (t("file.all"), "*.*")])
        if path:
            var.set(path)

    def _save(self) -> None:
        values = {k: v.get().strip() for k, v in self.vars.items()}
        required = self.provider.requires_credentials()
        missing = [f for f in required if not values.get(f)]
        if missing:
            messagebox.showwarning(t("dialog.confirm"), t("provider.credentials_required"), parent=self)
            return
        config.set_provider_credentials(self.provider.name, values)
        if self.on_saved is not None:
            self.on_saved()
        self.destroy()


class TTSApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        set_language(config.get_last("ui_language"))
        self.root.title(f'{t("app.title")} v{VERSION}')
        self.root.geometry("780x780")

        self.chapters: list[Chapter] = []
        self.voices: list[dict] = []
        self.voice_cache: dict[str, list[dict]] = {}
        self.voice_request_id = 0
        self.cancel_event = threading.Event()
        self._output_signature: tuple[tuple[int, str, str], ...] = ()
        self._checked_output_rows: set[int] = set()

        self._build_widgets()

        last = config.get_last("last_provider") or "edge"
        names = [n for n, _label in all_providers()]
        if last in names:
            self.var_provider.set(self._name_to_label[last])
        else:
            self.var_provider.set(self._name_to_label["edge"])
        self.root.after(100, lambda: self._on_provider_changed(initial=True))

    def _open_support_url(self, url: str) -> None:
        try:
            if webbrowser.open(url):
                return
        except webbrowser.Error:
            pass
        self._show_support_open_failed(url)

    def _open_support(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(t("support.dialog_title"))
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("support.dialog_message"), wraplength=380).pack(
            fill="x", pady=(0, 10)
        )
        for label, url in SUPPORT_LINKS:
            ttk.Button(
                frame,
                text=label,
                command=lambda target=url: (dialog.destroy(), self._open_support_url(target)),
            ).pack(fill="x", pady=3)
        ttk.Button(frame, text=t("support.close"), command=dialog.destroy).pack(
            side="right", pady=(10, 0)
        )

    def _show_support_open_failed(self, url: str) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(t("support.open_failed_title"))
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("support.open_failed_message"), wraplength=420).pack(
            fill="x", pady=(0, 8)
        )
        url_entry = ttk.Entry(frame, width=54)
        url_entry.insert(0, url)
        url_entry.config(state="readonly")
        url_entry.pack(fill="x")

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(
            buttons,
            text=t("support.copy"),
            command=lambda: (self.root.clipboard_clear(), self.root.clipboard_append(url)),
        ).pack(side="left")
        ttk.Button(buttons, text=t("support.close"), command=dialog.destroy).pack(side="right")

    def _build_widgets(self) -> None:
        pad = {"padx": 8, "pady": 4}

        frm_language = ttk.Frame(self.root)
        frm_language.pack(fill="x", padx=8, pady=(6, 0))
        ttk.Label(frm_language, text=t("language.label")).pack(side="left", padx=(6, 4))
        self.var_ui_language = tk.StringVar(value=LANGUAGE_NAMES[set_language(config.get_last("ui_language"))])
        self.cmb_ui_language = ttk.Combobox(
            frm_language,
            state="readonly",
            width=14,
            values=[LANGUAGE_NAMES[language] for language in SUPPORTED_LANGUAGES],
            textvariable=self.var_ui_language,
        )
        self.cmb_ui_language.pack(side="left")
        self.cmb_ui_language.bind("<<ComboboxSelected>>", self._on_ui_language_changed)
        ttk.Button(
            frm_language, text=t("app.support"), command=self._open_support,
            style="Toolbutton",
        ).pack(side="right", padx=(8, 0))
        ttk.Label(frm_language, text=f"v{VERSION}", foreground="#666666").pack(side="right")

        frm_prov = ttk.LabelFrame(self.root, text=t("provider.group"))
        frm_prov.pack(fill="x", **pad)
        self.var_provider = tk.StringVar()
        providers = all_providers()
        name_to_label = dict(providers)
        self._name_to_label = name_to_label
        self.cmb_provider = ttk.Combobox(
            frm_prov,
            state="readonly",
            width=24,
            values=[label for _n, label in providers],
            textvariable=self.var_provider,
        )
        self.cmb_provider.pack(side="left", padx=6, pady=6)
        self.cmb_provider.bind("<<ComboboxSelected>>", lambda _e: self._on_provider_changed())
        ttk.Button(frm_prov, text=t("provider.settings"), command=self.on_open_settings).pack(
            side="left", padx=6, pady=6
        )

        frm_file = ttk.LabelFrame(self.root, text=t("input.group"))
        frm_file.pack(fill="x", **pad)
        self.var_filepath = tk.StringVar()
        ttk.Entry(frm_file, textvariable=self.var_filepath, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6, pady=6
        )
        ttk.Button(frm_file, text=t("browse"), command=self.on_browse_file).pack(
            side="left", padx=(0, 6), pady=6
        )

        frm_out = ttk.LabelFrame(self.root, text=t("output.group"))
        frm_out.pack(fill="x", **pad)
        default_out = config.get_last("last_output_dir") or os.path.join(
            os.path.expanduser("~"), "Documents", "tts-mp3"
        )
        self.var_outdir = tk.StringVar(value=default_out)
        ttk.Entry(frm_out, textvariable=self.var_outdir).pack(
            side="left", fill="x", expand=True, padx=6, pady=6
        )
        ttk.Button(frm_out, text=t("browse"), command=self.on_browse_outdir).pack(
            side="left", padx=(0, 6), pady=6
        )

        frm_split = ttk.LabelFrame(self.root, text=t("split.group"))
        frm_split.pack(fill="x", **pad)
        saved_mode = config.get_last("last_split_mode")
        if saved_mode not in ("chapter", "chars"):
            saved_mode = "chapter"
        saved_chars = config.get_last("last_split_chars")
        if not isinstance(saved_chars, int) or isinstance(saved_chars, bool) or saved_chars <= 0:
            saved_chars = 5000
        self.var_split_mode = tk.StringVar(value=saved_mode)
        self.var_split_chars = tk.StringVar(value=str(saved_chars))
        ttk.Radiobutton(
            frm_split,
            text=t("split.chapter"),
            variable=self.var_split_mode,
            value="chapter",
            command=self._on_split_settings_changed,
        ).pack(side="left", padx=(6, 12), pady=6)
        ttk.Radiobutton(
            frm_split,
            text=t("split.chars"),
            variable=self.var_split_mode,
            value="chars",
            command=self._on_split_settings_changed,
        ).pack(side="left", padx=(0, 6), pady=6)
        self.entry_split_chars = ttk.Entry(
            frm_split, textvariable=self.var_split_chars, width=10
        )
        self.entry_split_chars.pack(side="left", padx=(0, 4), pady=6)
        ttk.Label(frm_split, text=t("split.chars_suffix")).pack(side="left", pady=6)
        self.entry_split_chars.bind("<KeyRelease>", lambda _e: self._on_split_settings_changed())
        self.entry_split_chars.bind("<FocusOut>", lambda _e: self._on_split_settings_changed())
        self.entry_split_chars.bind("<Return>", lambda _e: self._on_split_settings_changed())
        self._update_split_entry_state()

        frm_voice = ttk.LabelFrame(self.root, text=t("audio.group"))
        frm_voice.pack(fill="x", **pad)

        ttk.Label(frm_voice, text=t("audio.language")).grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.cmb_lang = ttk.Combobox(frm_voice, state="readonly", width=14)
        self.cmb_lang.grid(row=0, column=1, padx=(0, 12), pady=6, sticky="w")
        self.cmb_lang.bind("<<ComboboxSelected>>", lambda _e: self._update_voice_list())

        ttk.Label(frm_voice, text=t("audio.voice")).grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.cmb_voice = ttk.Combobox(frm_voice, state="readonly", width=32)
        self.cmb_voice.grid(row=0, column=3, padx=(0, 12), pady=6, sticky="w")

        self.var_rate = tk.DoubleVar(value=0)
        self.var_volume = tk.DoubleVar(value=0)
        self.var_pitch = tk.DoubleVar(value=0)
        for row, (label, var, lo, hi, suffix) in enumerate(
            [
                (t("audio.rate"), self.var_rate, -50, 50, "%"),
                (t("audio.volume"), self.var_volume, -50, 50, "%"),
                (t("audio.pitch"), self.var_pitch, -50, 50, "Hz"),
            ],
            start=1,
        ):
            ttk.Label(frm_voice, text=label).grid(row=row, column=0, columnspan=2, padx=6, sticky="w")
            scale = ttk.Scale(frm_voice, from_=lo, to=hi, variable=var, orient="horizontal")
            scale.grid(row=row, column=2, columnspan=2, sticky="we", padx=6, pady=2)
            lbl_val = ttk.Label(frm_voice, width=8)
            lbl_val.grid(row=row, column=4, padx=6, sticky="w")
            var.trace_add(
                "write",
                lambda *_a, v=var, l=lbl_val, s=suffix: l.config(text=f"{int(v.get()):+d}{s}"),
            )
        frm_voice.columnconfigure(3, weight=1)

        frm_ch = ttk.LabelFrame(self.root, text=t("units.group"))
        frm_ch.pack(fill="both", expand=True, **pad)
        frm_ch_actions = ttk.Frame(frm_ch)
        frm_ch_actions.pack(fill="x", padx=6, pady=(6, 0))
        ttk.Button(frm_ch_actions, text=t("button.check_all"), command=self._check_all_output_rows).pack(side="left")
        ttk.Button(frm_ch_actions, text=t("button.uncheck_all"), command=self._uncheck_all_output_rows).pack(side="left", padx=(6, 0))
        self.tree = ttk.Treeview(frm_ch, columns=("checked", "no", "title", "chars"), show="headings", height=7)
        self.tree.heading("checked", text="")
        self.tree.heading("no", text="#")
        self.tree.heading("title", text=t("units.title"))
        self.tree.heading("chars", text=t("units.chars"))
        self.tree.column("checked", width=36, minwidth=36, stretch=False, anchor="center")
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("title", width=480)
        self.tree.column("chars", width=70, anchor="e")
        sb = ttk.Scrollbar(frm_ch, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Button-1>", self._on_output_tree_click)
        self.tree.bind("<space>", self._on_output_tree_space)
        self.tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        sb.pack(side="right", fill="y", pady=6, padx=(0, 6))

        frm_run = ttk.Frame(self.root)
        frm_run.pack(fill="x", **pad)
        self.btn_preview = ttk.Button(frm_run, text=t("button.preview"), command=self.on_preview)
        self.btn_preview.pack(side="left", padx=6)
        self.btn_generate = ttk.Button(frm_run, text=t("button.generate"), command=self.on_generate)
        self.btn_generate.pack(side="left", padx=6)
        self.btn_cancel = ttk.Button(frm_run, text=t("button.cancel"), command=self.on_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=6)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", **pad)
        self.var_status = tk.StringVar(value=t("status.ready"))
        ttk.Label(self.root, textvariable=self.var_status, anchor="w").pack(fill="x", padx=10)

    def _current_provider_name(self) -> str:
        label = self.var_provider.get()
        for name, lbl in self._name_to_label.items():
            if lbl == label:
                return name
        return "edge"

    def _on_ui_language_changed(self, _event=None) -> None:
        selected_name = self.var_ui_language.get()
        language = next(
            (code for code, name in LANGUAGE_NAMES.items() if name == selected_name),
            "en",
        )
        if language == config.get_last("ui_language"):
            return

        provider_name = self._current_provider_name()
        filepath = self.var_filepath.get()
        outdir = self.var_outdir.get()
        rate = self.var_rate.get()
        volume = self.var_volume.get()
        pitch = self.var_pitch.get()
        config.set_last("ui_language", language)
        set_language(language)
        self.voice_request_id += 1
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(f'{t("app.title")} v{VERSION}')
        self._build_widgets()
        self.var_provider.set(self._name_to_label.get(provider_name, self._name_to_label["edge"]))
        self.var_filepath.set(filepath)
        self.var_outdir.set(outdir)
        self.var_rate.set(rate)
        self.var_volume.set(volume)
        self.var_pitch.set(pitch)
        self._refresh_output_list()
        self.root.after(0, lambda: self._on_provider_changed(initial=True))

    def _current_provider(self):
        return get_provider(self._current_provider_name())

    def _credentials_ready(self, provider) -> bool:
        saved = config.get_provider_credentials(provider.name)
        return all(saved.get(f, "").strip() for f in provider.requires_credentials())

    def _on_provider_changed(self, initial: bool = False) -> None:
        provider = self._current_provider()
        config.set_last("last_provider", provider.name)
        self.voices = []
        self.cmb_voice["values"] = []
        self.cmb_lang["values"] = []

        def open_settings_then_load() -> None:
            SettingsDialog(
                self.root,
                provider,
                on_saved=lambda: self._reload_provider_voices(provider),
            )

        if not self._credentials_ready(provider):
            if initial:
                self.root.after(200, open_settings_then_load)
            else:
                open_settings_then_load()
            self.var_status.set(t("provider.credentials_missing", provider=provider.label))
            return
        self._load_voices_async(provider)

    def on_open_settings(self) -> None:
        provider = self._current_provider()
        SettingsDialog(
            self.root,
            provider,
            on_saved=lambda: self._reload_provider_voices(provider),
        )

    def _reload_provider_voices(self, provider) -> None:
        self.voice_cache.pop(provider.name, None)
        self._load_voices_async(provider)

    def _load_voices_async(self, provider) -> None:
        self.voice_request_id += 1
        request_id = self.voice_request_id
        cached = self.voice_cache.get(provider.name)
        if cached is not None:
            self._voices_loaded(cached, provider, request_id)
            return

        def worker() -> None:
            try:
                provider.validate_credentials()
                voices = provider.list_voices()
            except Exception as e:
                self.root.after(
                    0,
                    lambda err=e, p=provider, rid=request_id: self._voices_failed(
                        err, p, rid
                    ),
                )
                return
            self.root.after(
                0,
                lambda vs=voices, p=provider, rid=request_id: self._voices_loaded(
                    vs, p, rid
                ),
            )

        self.var_status.set(t("provider.voices_loading"))
        threading.Thread(target=worker, daemon=True).start()

    def _voices_failed(self, err: Exception, provider, request_id: int) -> None:
        if request_id != self.voice_request_id:
            return
        if self._current_provider_name() != provider.name:
            return
        self.var_status.set(t("provider.voices_failed", provider=provider.label, error=err))

    def _voices_loaded(self, voices: list[dict], provider, request_id: int) -> None:
        if request_id != self.voice_request_id:
            return
        if self._current_provider_name() != provider.name:
            return
        self.voice_cache[provider.name] = voices
        self.voices = voices
        codes = ["all"] + get_language_codes(voices)
        self.cmb_lang["values"] = codes
        default = "ja-JP" if "ja-JP" in codes else ("en-US" if "en-US" in codes else "all")
        self.cmb_lang.set(default)
        self._update_voice_list()
        self.var_status.set(t("provider.ready", provider=provider.label, count=len(voices)))

    def _update_voice_list(self) -> None:
        filtered = voices_for_locale(self.voices, self.cmb_lang.get())
        display = [f"{v['ShortName']}  ({v.get('Gender', '')})" for v in filtered]
        self.cmb_voice["values"] = display
        if display:
            self.cmb_voice.current(0)

    def _parse_split_chars(self, *, show_warning: bool = False) -> int | None:
        try:
            value = int(self.var_split_chars.get().strip())
            if value <= 0:
                raise ValueError
        except ValueError:
            if show_warning:
                messagebox.showwarning(t("dialog.confirm"), t("status.invalid_chars"))
            return None
        return value

    def _output_chapters(self, *, show_warning: bool = False) -> list[Chapter] | None:
        if self.var_split_mode.get() == "chapter":
            return self.chapters
        max_chars = self._parse_split_chars(show_warning=show_warning)
        if max_chars is None:
            return None
        return split_chapters_by_chars(self.chapters, max_chars)

    def _update_split_entry_state(self) -> None:
        state = "normal" if self.var_split_mode.get() == "chars" else "disabled"
        self.entry_split_chars.config(state=state)

    def _on_split_settings_changed(self) -> None:
        self._update_split_entry_state()
        mode = self.var_split_mode.get()
        config.set_last("last_split_mode", mode)
        max_chars = self._parse_split_chars()
        if max_chars is not None:
            config.set_last("last_split_chars", max_chars)
        self._refresh_output_list()

    def _refresh_output_list(self) -> None:
        self.tree.delete(*self.tree.get_children())
        output_chapters = self._output_chapters()
        if output_chapters is None:
            self.var_status.set(t("status.invalid_chars"))
            return
        signature = tuple((ch.index, ch.title, ch.text) for ch in output_chapters)
        if signature != self._output_signature:
            self._output_signature = signature
            self._checked_output_rows = set(range(len(output_chapters)))
        for row, ch in enumerate(output_chapters):
            checked = "☑" if row in self._checked_output_rows else "☐"
            self.tree.insert("", "end", iid=str(row), values=(checked, ch.index, ch.title, len(ch.text)))
        if not self.chapters:
            return
        total_chars = (
            sum(len(c.text) for c in self.chapters)
            if self.var_split_mode.get() == "chapter"
            else sum(len(c.text) for c in output_chapters)
        )
        unit_label = t("unit.chapters") if self.var_split_mode.get() == "chapter" else t("unit.files")
        self.var_status.set(t("status.units", count=len(output_chapters), unit=unit_label, chars=total_chars))

    def _toggle_output_row(self, row: int) -> None:
        if str(self.btn_generate.cget("state")) == "disabled":
            return
        if row in self._checked_output_rows:
            self._checked_output_rows.remove(row)
        else:
            self._checked_output_rows.add(row)
        item = str(row)
        if self.tree.exists(item):
            values = list(self.tree.item(item, "values"))
            values[0] = "☑" if row in self._checked_output_rows else "☐"
            self.tree.item(item, values=values)

    def _set_all_output_rows_checked(self, checked: bool) -> None:
        if str(self.btn_generate.cget("state")) == "disabled":
            return
        rows = range(len(self._output_signature))
        self._checked_output_rows = set(rows) if checked else set()
        for row in rows:
            item = str(row)
            if self.tree.exists(item):
                values = list(self.tree.item(item, "values"))
                values[0] = "☑" if checked else "☐"
                self.tree.item(item, values=values)

    def _check_all_output_rows(self) -> None:
        self._set_all_output_rows_checked(True)

    def _uncheck_all_output_rows(self) -> None:
        self._set_all_output_rows_checked(False)

    def _on_output_tree_click(self, event) -> None:
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        item = self.tree.identify_row(event.y)
        if item:
            self._toggle_output_row(int(item))

    def _on_output_tree_space(self, _event) -> str:
        for item in self.tree.selection():
            self._toggle_output_row(int(item))
        return "break"

    def _mark_output_row_completed(self, row: int) -> None:
        self._checked_output_rows.discard(row)
        item = str(row)
        if self.tree.exists(item):
            values = list(self.tree.item(item, "values"))
            values[0] = "☐"
            self.tree.item(item, values=values)

    def on_browse_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                (t("file.supported"), "*.txt *.epub *.pdf *.mobi *.azw *.azw3"),
                (t("file.text"), "*.txt"),
                ("EPUB", "*.epub"),
                ("PDF", "*.pdf"),
                ("MOBI/AZW/AZW3", "*.mobi *.azw *.azw3"),
            ]
        )
        if not path:
            return
        try:
            chapters = load_chapters(path)
        except Exception as e:
            messagebox.showerror(t("dialog.error"), str(e))
            return
        self.chapters = chapters
        self._output_signature = ()
        self.var_filepath.set(path)
        self._refresh_output_list()

    def on_browse_outdir(self) -> None:
        d = filedialog.askdirectory()
        if d:
            self.var_outdir.set(d)

    def on_preview(self) -> None:
        if not self.chapters:
            messagebox.showwarning(t("dialog.confirm"), t("error.input_required"))
            return
        if not self.cmb_voice.get():
            messagebox.showwarning(t("dialog.confirm"), t("error.voice_required"))
            return

        output_chapters = self._output_chapters(show_warning=True)
        if not output_chapters:
            return
        selected = self.tree.selection()
        selected_index = self.tree.index(selected[0]) if selected else 0
        if selected_index >= len(output_chapters):
            selected_index = 0
        rate_value = int(self.var_rate.get())
        preview_chars = max(1, int(75 * (1 + rate_value / 100)))
        preview_text = extract_preview_text(
            output_chapters[selected_index].text,
            max_chars=preview_chars,
        )
        if not preview_text:
            messagebox.showwarning(t("dialog.confirm"), t("error.preview_text"))
            return

        voice = self.cmb_voice.get().split()[0]
        rate = f"{rate_value:+d}%"
        volume = f"{int(self.var_volume.get()):+d}%"
        pitch = f"{int(self.var_pitch.get()):+d}Hz"
        try:
            provider = self._current_provider()
            provider.validate_credentials()
        except ProviderError as e:
            self.on_open_settings()
            messagebox.showwarning(t("dialog.confirm"), str(e))
            return

        self._start_operation(t("preview.generating"))

        def done(path: str) -> None:
            def ui() -> None:
                self._finish()
                try:
                    self._play_audio(path)
                    self.var_status.set(t("preview.playing"))
                except OSError as e:
                    self.var_status.set(t("preview.play_error", error=e))
                    messagebox.showerror(t("preview.play_error_title"), str(e))

            self.root.after(0, ui)

        def failed(err: BaseException, path: str) -> None:
            def ui() -> None:
                self._finish()
                if isinstance(err, CancelledError):
                    self.var_status.set(t("preview.cancelled"))
                else:
                    self.var_status.set(t("preview.error", error=err))
                    messagebox.showerror(t("preview.error_title"), str(err))

            try:
                os.remove(path)
            except OSError:
                pass
            self.root.after(0, ui)

        def run() -> None:
            fd, path = tempfile.mkstemp(prefix="tts-text-mp3-preview-", suffix=".mp3")
            os.close(fd)
            try:
                provider.generate_audio(
                    preview_text,
                    voice,
                    path,
                    rate=rate,
                    volume=volume,
                    pitch=pitch,
                    cancel_event=self.cancel_event,
                )
                done(path)
            except BaseException as e:
                failed(e, path)

        threading.Thread(target=run, daemon=True).start()

    @staticmethod
    def _play_audio(path: str) -> None:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def on_generate(self) -> None:
        if not self.chapters:
            messagebox.showwarning(t("dialog.confirm"), t("error.input_required"))
            return
        if not self.cmb_voice.get():
            messagebox.showwarning(t("dialog.confirm"), t("error.voice_required"))
            return
        output_chapters = self._output_chapters(show_warning=True)
        if not output_chapters:
            return
        selected_rows = sorted(self._checked_output_rows)
        selected_units = [output_chapters[row] for row in selected_rows if row < len(output_chapters)]
        if not selected_units:
            messagebox.showwarning(t("dialog.confirm"), t("error.no_units_checked"))
            return
        voice = self.cmb_voice.get().split()[0]
        out_dir = self.var_outdir.get().strip() or "."
        rate = f"{int(self.var_rate.get()):+d}%"
        volume = f"{int(self.var_volume.get()):+d}%"
        pitch = f"{int(self.var_pitch.get()):+d}Hz"
        try:
            provider = self._current_provider()
            provider.validate_credentials()
        except ProviderError as e:
            self.on_open_settings()
            messagebox.showwarning(t("dialog.confirm"), str(e))
            return

        config.set_last("last_output_dir", out_dir)
        config.set_last("last_split_mode", self.var_split_mode.get())
        if self.var_split_mode.get() == "chars":
            config.set_last("last_split_chars", self._parse_split_chars())
        self._start_operation(t("generate.starting"))

        def chapter_cb(i: int, total: int, title: str) -> None:
            def ui() -> None:
                self.var_status.set(t("generate.progress", current=i, total=total, title=title))

            self.root.after(0, ui)

        def completed_cb(i: int, total: int, _chapter: Chapter, _path: str) -> None:
            row = selected_rows[i - 1]
            self.root.after(0, lambda r=row: self._mark_output_row_completed(r))

        def done(outputs: list[str]) -> None:
            def ui() -> None:
                self._finish()
                self.var_status.set(t("generate.done", count=len(outputs)))
                messagebox.showinfo(t("dialog.complete"), t("generate.done_message", count=len(outputs), directory=out_dir))

            self.root.after(0, ui)

        def failed(err: BaseException) -> None:
            def ui() -> None:
                self._finish()
                if isinstance(err, CancelledError):
                    self.var_status.set(t("generate.cancelled"))
                else:
                    self.var_status.set(t("generate.error", error=err))
                    messagebox.showerror(t("dialog.error"), str(err))

            self.root.after(0, ui)

        def run() -> None:
            try:
                outputs = generate_chapters(
                    provider,
                    selected_units,
                    voice,
                    out_dir,
                    rate=rate,
                    volume=volume,
                    pitch=pitch,
                    chapter_cb=chapter_cb,
                    completed_cb=completed_cb,
                    cancel_event=self.cancel_event,
                )
                done(outputs)
            except BaseException as e:
                failed(e)

        threading.Thread(target=run, daemon=True).start()

    def _start_operation(self, status: str) -> None:
        self.cancel_event.clear()
        self.btn_preview.config(state="disabled")
        self.btn_generate.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self.cmb_ui_language.config(state="disabled")
        self.progress.start(50)
        self.var_status.set(status)

    def _finish(self) -> None:
        self.progress.stop()
        self.btn_preview.config(state="normal")
        self.btn_generate.config(state="normal")
        self.btn_cancel.config(state="disabled")
        self.cmb_ui_language.config(state="readonly")

    def on_cancel(self) -> None:
        self.cancel_event.set()
        self.var_status.set(t("generate.cancelling"))


def run_app() -> None:
    root = tk.Tk()
    TTSApp(root)
    root.mainloop()
