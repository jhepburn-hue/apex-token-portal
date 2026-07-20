from __future__ import annotations
import configparser
import os
import re
from pathlib import Path

try:
    from utils.prox_math import generate_hex_codes
except ImportError:
    generate_hex_codes = None

TERMINAL_INFO_TRA_ON = "0x83"
TERMINAL_INFO_TRA_OFF = "0x00"

def build_tra_tci(tci: str, tra_mode: bool) -> str:
    """
    Builds the INI partial config for Option 4 including TCI and terminal_info hex setting.
    """
    terminal_info = TERMINAL_INFO_TRA_ON if tra_mode else TERMINAL_INFO_TRA_OFF

    ini_content = f"""[rfid/hf/app/wallet]
    terminal_id = "{tci.strip()}"
    terminal_info = {terminal_info}
    """
    return ini_content

def ensure_section(cfg: configparser.ConfigParser, section: str):
    if not cfg.has_section(section):
        cfg.add_section(section)


def set_kv(cfg: configparser.ConfigParser, section: str, key: str, value: str):
    ensure_section(cfg, section)
    cfg.set(section, key, value)


def _emit_ini_sorted(
    cfg: configparser.ConfigParser,
    out_ini: Path,
    keys_entries: dict = None,
    prox_filter_block: str | None = None,
    notes_block: str | None = None,
):
    """Writes the INI file with ordered sections, alphabetical keys, and formatting."""
    KEYS_SEC = "keys"
    GROUP = [
        "rfid/hf/app/wallet",
        "rfid/hf/app/meridian",
        "rfid/hf/app/mifare_2go/generic",
    ]

    all_secs = cfg.sections()
    normal_secs = [s for s in all_secs if s.lower() != KEYS_SEC]
    normal_secs.sort(key=str.lower)

    lower_to_orig = {s.lower(): s for s in normal_secs}
    present_group = [
        lower_to_orig[g] for g in (g.lower() for g in GROUP) if g in lower_to_orig
    ]
    if present_group:
        anchor_idx = min(normal_secs.index(s) for s in present_group)
        for s in present_group:
            normal_secs.remove(s)
        ordered_present = [
            lower_to_orig[g] for g in (g.lower() for g in GROUP) if g in lower_to_orig
        ]
        normal_secs[anchor_idx:anchor_idx] = ordered_present

    out_lines: list[str] = []
    for sec in normal_secs:
        out_lines.append(f"[{sec}]\n")
        items = list(cfg.items(sec))
        enabled_items = [(k, v) for (k, v) in items if k.lower() == "enabled"]
        other_items = [(k, v) for (k, v) in items if k.lower() != "enabled"]
        other_items.sort(key=lambda kv: kv[0].lower())
        ordered_items = enabled_items + other_items

        for k, v in ordered_items:
            out_lines.append(f"{k} = {v}\n")
        out_lines.append("\n")

    if prox_filter_block:
        if not out_lines or not out_lines[-1].endswith("\n"):
            out_lines.append("\n")
        out_lines.append(
            prox_filter_block
            if prox_filter_block.endswith("\n")
            else prox_filter_block + "\n"
        )

    if keys_entries:
        ordered_slots = sorted(
            keys_entries.keys(), key=lambda x: int(re.sub(r"\D", "", x) or 0)
        )
        out_lines.append("\n[keys]\n")
        for slot in ordered_slots:
            out_lines.append(f"{slot} = {keys_entries[slot]}\n")

    if notes_block:
        if not out_lines or not out_lines[-1].endswith("\n"):
            out_lines.append("\n")
        out_lines.append(
            notes_block if notes_block.endswith("\n") else notes_block + "\n"
        )

    out_ini.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ini, "w") as f:
        f.write("".join(out_lines).rstrip() + "\n")


def build_partial_ini(default_ini: Path, out_dir: Path, form: dict) -> Path:
    """Constructs a partial configuration INI file matching the original portal definitions."""
    cfg = configparser.ConfigParser()
    file_name = []

    # 1. Anti-Passback
    ap_val = form.get("anti_passback", "").strip().lower()
    if ap_val == "enable":
        set_kv(cfg, "card_tracker", "enabled", "true")
        file_name.append("anti_passback_enabled")
    elif ap_val == "disable":
        set_kv(cfg, "card_tracker", "enabled", "false")
        file_name.append("anti_passback_disabled")

    # 2. BLE-Credentials
    ble_cred_val = form.get("ble_credentials", "").strip().lower()
    if ble_cred_val == "enable":
        set_kv(cfg, "ble/configure", "allow_credentials", "true")
        set_kv(cfg, "mypass", "allow_credentials", "true")
        set_kv(cfg, "mypass", "allow_key_rolling", "true")
        file_name.append("ble_credentials_enabled")
    elif ble_cred_val == "disable":
        set_kv(cfg, "ble/configure", "allow_credentials", "false")
        set_kv(cfg, "mypass", "allow_credentials", "false")
        set_kv(cfg, "mypass", "allow_key_rolling", "false")
        file_name.append("ble_credentials_disabled")

    # 3. BLE
    ble_val = form.get("ble", "").strip().lower()
    if ble_val == "enable":
        set_kv(cfg, "ble", "enabled", "true")
        file_name.append("ble_enabled")
    elif ble_val == "disable":
        set_kv(cfg, "ble", "enabled", "false")
        file_name.append("ble_disabled")

    # 4. Buzzer
    buzzer_val = form.get("buzzer", "").strip().lower()
    if buzzer_val == "enable":
        set_kv(cfg, "av", "silence_beeper", "false")
        file_name.append("buzzer_enabled")
    elif buzzer_val == "disable":
        set_kv(cfg, "av", "silence_beeper", "true")
        file_name.append("buzzer_disabled")

    # 5. CSN Logic
    csn_section = "rfid/hf/app/csn"
    mfc_val = form.get("mfc_csn", "").strip().lower()
    ev_val = form.get("ev_csn", "").strip().lower()
    iclass_val = form.get("iclass_csn", "").strip().lower()
    iso15693_val = form.get("iso15693_csn", "").strip().lower()
    iso1444a_val = form.get("iso14443a_csn", "").strip().lower()
    base_csn = form.get("csn", "").strip().lower()

    all_inputs = [mfc_val, ev_val, iclass_val, iso15693_val, iso1444a_val, base_csn]
    any_csn_enabled = any(v in ["on", "on_32", "on_56", "enable"] for v in all_inputs)

    if base_csn == "disable":
        set_kv(cfg, csn_section, "enabled", "false")
        file_name.append("csn_disabled")
    elif any_csn_enabled or base_csn == "enable":
        set_kv(cfg, csn_section, "enabled", "true")
        file_name.append("csn_enabled")

    def _resolve_format(states):
        filtered = [s for s in states if s]
        if not filtered:
            return None
        if any(s == "on_56" for s in filtered):
            return "0x3701"
        if any(s == "on_32" for s in filtered):
            return "0x2001"
        if any(s == "on" for s in filtered):
            return None
        if any(s == "off" for s in filtered):
            return "0xFFFF"
        return None

    mfc_fmt = _resolve_format([mfc_val])
    if mfc_fmt:
        set_kv(cfg, csn_section, "mifare_classic_format", mfc_fmt)

    cl_fmt = _resolve_format([ev_val, iso1444a_val])
    if cl_fmt:
        set_kv(cfg, csn_section, "iso14443a_cl1_format", cl_fmt)
        set_kv(cfg, csn_section, "iso14443a_cl2_format", cl_fmt)

    b_fmt = _resolve_format([ev_val])
    if b_fmt:
        set_kv(cfg, csn_section, "iso14443b_format", b_fmt)

    v_fmt = _resolve_format([iclass_val, iso15693_val])
    if v_fmt:
        set_kv(cfg, csn_section, "iso15693_format", v_fmt)

    pico_fmt = _resolve_format([iclass_val])
    if pico_fmt:
        set_kv(cfg, csn_section, "pico15693_format", pico_fmt)

    for prefix, val in [
        ("mfc", mfc_val),
        ("ev1_ev2", ev_val),
        ("iclass", iclass_val),
        ("iso15693", iso15693_val),
        ("iso14443a", iso1444a_val),
    ]:
        if val in ["on", "on_32", "on_56", "off"]:
            file_name.append(f"{prefix}_csn_{val}")

    csn_flags = form.get("csn_flags") or {}
    if any(
        v in ["on", "on_32", "on_56", "enable", "disable"]
        for v in [mfc_val, ev_val, iclass_val, iso15693_val, iso1444a_val]
    ):
        protocols = {"A"}
        ev_active = form.get("EV1/EV2 CSN", "").lower() == "on" or (
            isinstance(csn_flags, dict) and csn_flags.get("ev1ev2", "off") != "off"
        )
        iclass_active = form.get("iClass CSN", "").lower() == "on" or (
            isinstance(csn_flags, dict) and csn_flags.get("iclass", "off") != "off"
        )
        iso15693_active = form.get("ISO15693 CSN", "").lower() == "on" or (
            isinstance(csn_flags, dict) and csn_flags.get("iso15693", "off") != "off"
        )

        if ev_val in ["on", "on_32", "on_56"] or ev_active:
            protocols.add("B")
        if (
            iclass_val in ["on", "on_32", "on_56"]
            or iso15693_val in ["on", "on_32", "on_56"]
            or iclass_active
            or iso15693_active
        ):
            protocols.add("V")
        if {"A", "B", "V"}.issubset(protocols):
            protocols.add("F")

        proto_string = "".join(sorted(list(protocols)))
        set_kv(cfg, "rfid/hf/nfc", "enabled_protocols", f'"{proto_string}"')

    # 6. HF
    hf_val = form.get("hf", "").strip().lower()
    if hf_val == "enable":
        set_kv(cfg, "rfid/hf/nfc", "enabled", "true")
        file_name.append("hf_enabled")
    elif hf_val == "disable":
        set_kv(cfg, "rfid/hf/nfc", "enabled", "false")
        file_name.append("hf_disabled")

    # 7. Idle LED
    idle_led_val = form.get("idle_led", "").strip().lower()
    if idle_led_val != "":
        set_kv(cfg, "av", "idle_color", f'"{idle_led_val}"')
        file_name.append(f"idle_led_{idle_led_val}")

    # 8. Keypad Bit
    kp_val = form.get("keypad_bit", "").strip().lower()
    if kp_val != "":
        set_kv(cfg, "wiegand", "space_duration_us", "1000")
        set_kv(cfg, "wiegand", "pulse_duration_us", "60")
        set_kv(cfg, "wiegand", "lines_inverted", "false")
        set_kv(cfg, "wiegand", "red_ctrl_mode", "red")
        set_kv(cfg, "wiegand", "green_ctrl_mode", "green")
        set_kv(cfg, "wiegand", "buzzer_ctrl_mode", "buzzer")
        set_kv(cfg, "wiegand", "default_format", f"{kp_val}_bit")
        set_kv(cfg, "wiegand", "default_facility_code", "0")
        file_name.append(f"keypad_bit_{kp_val}")

    # 9. OSDP Address
    osdp_addr_val = form.get("osdp_address", "").strip().lower()
    if osdp_addr_val != "":
        set_kv(cfg, "osdp/comms", "addr", osdp_addr_val)
        file_name.append(f"osdp_address_{osdp_addr_val}")

    # 10. OSDP Baud Rate
    osdp_baud_val = form.get("osdp_baud_rate", "").strip().lower()
    if osdp_baud_val != "":
        set_kv(cfg, "osdp/comms", "baud_rate", osdp_baud_val)
        file_name.append(f"osdp_baud_rate_{osdp_baud_val}")

    # 11. Prox
    prox_val = form.get("prox", "").strip().lower()
    if prox_val == "enable":
        set_kv(cfg, "rfid/lf", "enabled", "true")
        file_name.append("prox_enabled")
    elif prox_val == "disable":
        set_kv(cfg, "rfid/lf", "enabled", "false")
        file_name.append("prox_disabled")

    # 12. Prox Filter
    if form.get("prox_filter_details") and generate_hex_codes:
        details = form.get("prox_filter_details")
        if isinstance(details, dict) and details.get("rules"):
            set_kv(cfg, "rfid/lf", "enabled", "true")
            file_name.append(f"prox_filter_{details['format'].lower()}")

            m_hex, v_hex = generate_hex_codes(details)
            rule = details["rules"][0]

            set_kv(cfg, "rfid/lf", "filter_mask", f'"{m_hex}"')
            set_kv(cfg, "rfid/lf", "filter_value", f'"{v_hex}"')
            set_kv(cfg, "rfid/lf", "filter_bit_len", str(details.get("bit_count", 40)))
            set_kv(cfg, "rfid/lf", "filter_enabled", "true")

            logic_map = {
                "GREATER_OR_EQUAL": '"greater_or_equal"',
                "LESS_OR_EQUAL": '"less_or_equal"',
                "EQUAL": '"equal"',
            }
            set_kv(
                cfg,
                "rfid/lf",
                "filter_function",
                logic_map.get(rule["logic"], '"equal"'),
            )

    # 13. Tamper
    tamper_val = form.get("tamper", "").strip().lower()
    if tamper_val == "enable":
        set_kv(cfg, "tamper", "wiegand_reporting_enabled", "true")
        set_kv(cfg, "tamper", "osdp_reporting_enabled", "true")
        file_name.append("tamper_enabled")
    elif tamper_val == "disable":
        set_kv(cfg, "tamper", "wiegand_reporting_enabled", "false")
        set_kv(cfg, "tamper", "osdp_reporting_enabled", "false")
        file_name.append("tamper_disabled")

    # 14. TCI and TRA Mode
    # 14. TCI and TRA Mode
    tci_value = form.get("tci", "").strip().lower()
    tra_mode_raw = form.get("tra_mode", "").strip().lower()

    if tci_value:
        set_kv(cfg, "rfid/hf/app/wallet", "terminal_id", f'"{tci_value}"')
        file_name.append(f"tci_{tci_value}")

    if tra_mode_raw in ["on", "off"]:
        tra_mode = tra_mode_raw == "on"
        terminal_info = TERMINAL_INFO_TRA_ON if tra_mode else TERMINAL_INFO_TRA_OFF
        
        set_kv(cfg, "rfid/hf/app/wallet", "terminal_info", terminal_info)
        file_name.append("tra_on" if tra_mode else "tra_off")

    if out_dir.suffix == ".ini":
        out_dir = out_dir.parent

    base_name = "_".join(file_name) if file_name else "partial_config"
    out_ini = out_dir / f"{base_name}.ini"

    _emit_ini_sorted(cfg, out_ini, {}, None, None)
    return out_ini