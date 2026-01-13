# FlooAuxInput.py — duplex audio streaming for Linux (Debian)
# Public API:
#   - list_additional_inputs(), serialize_input_device()
#   - set_input(selection), set_blocksize(n), stop()
# Optional helper:
#   - set_output_mapping([3,4])  # force device channel mapping if needed

import logging
from collections.abc import Sequence

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class FlooAuxInput:
    TARGET_RATE = 48000
    FALLBACK_RATE = 44100
    DTYPE = "int16"
    LATENCY = None

    PREFERRED_INPUT_BACKENDS = ["ALSA", "JACK", "PulseAudio"]
    PREFERRED_OUTPUT_BACKENDS = ["ALSA", "JACK", "PulseAudio"]

    # Output auto-pick (name hints)
    OUTPUT_HINTS: Sequence[str] = ("FMA120", "QCC3086")

    # Hide these from input list
    INPUT_BLOCKLIST = ("FMA120", "QCC3086")

    _DISABLED = object()

    @staticmethod
    def _platform_default_blocksize() -> int:
        return 256

    @staticmethod
    def _validate_blocksize(n: int) -> int:
        if not isinstance(n, int):
            raise ValueError("blocksize must be an integer")
        if n < 64:
            raise ValueError("blocksize too small (min 64)")
        if n > 4096:
            raise ValueError("blocksize too large (max 4096)")
        return n

    def __init__(self, blocksize: int | None = None):
        self._stream: sd.Stream | None = None
        self._running = False

        self._cap_channels = 1
        self._pb_channels = 2
        self._rate = self.TARGET_RATE
        self._dtype = self.DTYPE

        self._input_sel: dict | None = None
        self._input_disabled = False

        self._blocksize = (
            self._platform_default_blocksize()
            if blocksize is None
            else self._validate_blocksize(blocksize)
        )

        self._last_start_name_hint: str | None = None

        self._xruns = 0
        self._debug = False

        self._out_mapping: list[int] | None = None

    # ------- Optional helper -------
    def set_output_mapping(self, mapping: Sequence[int] | None) -> None:
        """Optionally force output channel indices (1-based), e.g. [3,4]."""
        self._out_mapping = list(mapping) if mapping else None

    # -------------- Public API --------------

    def list_additional_inputs(self) -> list[dict]:
        devs = self._sd_list_devices()
        chosen_backend = None
        available = {d["hostapi"] for d in devs if d["is_input"]}
        for b in self.PREFERRED_INPUT_BACKENDS:
            if b in available:
                chosen_backend = b
                break

        if chosen_backend:
            candidates = [
                d
                for d in devs
                if d["is_input"]
                and d["hostapi"] == chosen_backend
                and not self._is_blocklisted_input(d["name"])
            ]
        else:
            candidates = [
                d for d in devs if d["is_input"] and not self._is_blocklisted_input(d["name"])
            ]

        out: list[dict] = [
            {
                "id": None,
                "name": "None",
                "backend": "",
                "sample_rate": None,
                "max_channels": None,
            }
        ]
        for d in candidates:
            out.append(
                {
                    "id": d["index"],
                    "name": d["name"],
                    "backend": d["hostapi"],
                    "sample_rate": d["default_samplerate"],
                    "max_channels": d["max_input_channels"],
                }
            )
        return out

    def serialize_input_device(self, device: dict | None) -> dict:
        if (
            (not device)
            or (device.get("id") is None)
            or (device.get("name", "").strip().lower() == "none")
        ):
            return {"id": None, "name": "None", "backend": ""}
        return {
            "id": device.get("id"),
            "name": device.get("name", ""),
            "backend": device.get("backend", ""),
        }

    def set_input(self, selection: dict | None) -> None:
        was_running = self._running

        if selection is None or self._is_saved_disabled(selection):
            self._input_sel = {"id": None, "name": "None", "backend": ""}
            self._input_disabled = True
            if was_running:
                self.stop()
            logger.info("Input set to 'None' - loop disabled.")
            return

        self._input_disabled = False
        self._input_sel = {
            "id": selection.get("id"),
            "name": selection.get("name", ""),
            "backend": selection.get("backend", ""),
        }

        if was_running:
            logger.info("Input changed - restarting loop...")
            self.stop()

        name_hint = self._input_sel["name"] or None
        self._last_start_name_hint = name_hint
        self._start_loop_internal(name_hint=name_hint)

    def set_blocksize(self, blocksize: int) -> None:
        """Update blocksize (frames per block) and restart if running."""
        new_bs = self._validate_blocksize(blocksize)
        if new_bs == self._blocksize:
            return
        self._blocksize = new_bs
        logger.debug("Blocksize set: %d", new_bs)
        if self._running:
            hint = self._last_start_name_hint
            self.stop()
            self._start_loop_internal(name_hint=hint)

    def stop(self) -> None:
        if not self._running:
            return
        try:
            if self._stream:
                try:
                    self._stream.stop()
                except sd.PortAudioError:
                    pass
                try:
                    self._stream.close()
                except sd.PortAudioError:
                    pass
        finally:
            self._stream = None
            self._running = False
            logger.debug("Loop stopped.")

    def _start_loop_internal(self, *, name_hint: str | None) -> None:
        if self._input_disabled:
            logger.debug("Not starting: input is 'None'.")
            return

        dtype = self.DTYPE
        latency = self.LATENCY
        chosen_block = self._blocksize

        add_in = (
            self._pick_best_input_for_hint(name_hint)
            or self._resolve_input_by_selection_or_hint(self._input_sel, name_hint)
            or self._first_ok_input()
        )
        out_dev = self._pick_output(self.OUTPUT_HINTS)
        if add_in is None or out_dev is None:
            logger.error("No valid input or output device.")
            return

        in_dev_info = sd.query_devices(add_in["id"])
        out_dev_info = sd.query_devices(out_dev["id"])
        self._cap_channels = 2 if int(in_dev_info.get("max_input_channels", 1)) >= 2 else 1
        self._pb_channels = 2 if int(out_dev_info.get("max_output_channels", 2)) >= 2 else 1

        logger.info(
            "Using Input: %s [%s] (%d ch)", add_in["name"], add_in["backend"], self._cap_channels
        )
        logger.info(
            "Using Output: %s [%s] (%d ch)", out_dev["name"], out_dev["backend"], self._pb_channels
        )

        rate = self._pick_common_rate(
            add_in["id"], out_dev["id"], dtype, self._cap_channels, self._pb_channels
        )
        if rate is None:
            logger.warning("No common sample rate (48k or 44.1k). Not starting.")
            return
        self._rate = rate
        self._dtype = dtype

        self._start_duplex(add_in, out_dev, chosen_block, latency)

    def _start_duplex(self, add_in, out_dev, chosen_block, latency):
        def duplex_cb(indata, outdata, frames, time_info, status):
            if status:
                self._xruns += 1
            if indata.shape[1] == outdata.shape[1]:
                outdata[:] = indata
                return
            if indata.shape[1] == 1 and outdata.shape[1] == 2:
                outdata[:, 0] = indata[:, 0]
                outdata[:, 1] = indata[:, 0]
                return
            if indata.shape[1] == 2 and outdata.shape[1] == 1:
                outdata[:, 0] = np.clip(
                    (indata[:, 0].astype(np.int32) + indata[:, 1].astype(np.int32)) // 2,
                    -32768, 32767
                ).astype(np.int16)

        sd.check_input_settings(
            device=add_in["id"],
            samplerate=self._rate,
            channels=self._cap_channels,
            dtype=self._dtype,
        )
        sd.check_output_settings(
            device=out_dev["id"],
            samplerate=self._rate,
            channels=self._pb_channels,
            dtype=self._dtype,
        )

        self._stream = sd.Stream(
            device=(add_in["id"], out_dev["id"]),
            samplerate=self._rate,
            blocksize=chosen_block,
            dtype=self._dtype,
            channels=(self._cap_channels, self._pb_channels),
            latency=latency,
            callback=duplex_cb,
        )
        self._stream.start()
        self._running = True
        logger.info(
            "Loop started @ %d Hz | block=%d | dtype=%s | latency=%s",
            self._rate,
            chosen_block,
            self._dtype,
            latency,
        )

    # -------------- Selection & Utilities --------------

    def _sd_list_devices(self) -> list[dict]:
        def norm(name: str) -> str:
            n = (name or "").lower()
            if "alsa" in n:
                return "ALSA"
            if "jack" in n:
                return "JACK"
            if "pulse" in n:
                return "PulseAudio"
            return name or ""

        has = sd.query_hostapis()
        result = []
        for idx, d in enumerate(sd.query_devices()):
            backend_short = norm(has[d["hostapi"]]["name"])
            result.append(
                {
                    "index": idx,
                    "name": d["name"],
                    "hostapi": backend_short,
                    "max_input_channels": int(d.get("max_input_channels", 0)),
                    "max_output_channels": int(d.get("max_output_channels", 0)),
                    "default_samplerate": float(d.get("default_samplerate", 0.0)) or None,
                    "is_input": int(d.get("max_input_channels", 0)) > 0,
                    "is_output": int(d.get("max_output_channels", 0)) > 0,
                }
            )
        return result

    @staticmethod
    def _is_blocklisted_input(name: str) -> bool:
        return any(tok.lower() in (name or "").lower() for tok in FlooAuxInput.INPUT_BLOCKLIST)

    @staticmethod
    def _is_saved_disabled(saved: dict) -> bool:
        return (
            (not saved)
            or (saved.get("id") is None)
            or (saved.get("name", "").strip().lower() == "none")
        )

    def _resolve_input_by_selection_or_hint(
        self, selection: dict | None, hint: str | None
    ) -> dict | None:
        if selection and not self._is_saved_disabled(selection):
            current = self.list_additional_inputs()[1:]
            for d in current:
                if d["name"] == selection.get("name") and d["id"] == selection.get("id"):
                    return d
        if hint:
            for d in self._sd_list_devices():
                if (
                    d["is_input"]
                    and hint.lower() in d["name"].lower()
                    and not self._is_blocklisted_input(d["name"])
                ):
                    return {
                        "id": d["index"],
                        "name": d["name"],
                        "backend": d["hostapi"],
                        "max_channels": d["max_input_channels"],
                        "default_samplerate": d["default_samplerate"],
                    }
        return None

    def _first_ok_input(self) -> dict | None:
        items = self.list_additional_inputs()
        return items[1] if len(items) > 1 else None

    def _pick_output(self, hints: Sequence[str]) -> dict | None:
        hints_l = [h.lower() for h in hints]
        devs = self._sd_list_devices()

        def match_exact(d):
            return any(d["name"].lower() == h for h in hints_l)

        def match_sub(d):
            return any(h in d["name"].lower() for h in hints_l)

        for b in self.PREFERRED_OUTPUT_BACKENDS:
            for d in devs:
                if d["is_output"] and d["hostapi"] == b and match_exact(d):
                    return {
                        "id": d["index"],
                        "name": d["name"],
                        "backend": d["hostapi"],
                        "sample_rate": d["default_samplerate"],
                        "max_channels": d["max_output_channels"],
                    }
        for b in self.PREFERRED_OUTPUT_BACKENDS:
            for d in devs:
                if d["is_output"] and d["hostapi"] == b and match_sub(d):
                    return {
                        "id": d["index"],
                        "name": d["name"],
                        "backend": d["hostapi"],
                        "sample_rate": d["default_samplerate"],
                        "max_channels": d["max_output_channels"],
                    }
        for d in devs:
            if d["is_output"] and match_exact(d):
                return {
                    "id": d["index"],
                    "name": d["name"],
                    "backend": d["hostapi"],
                    "sample_rate": d["default_samplerate"],
                    "max_channels": d["max_output_channels"],
                }
        for d in devs:
            if d["is_output"] and match_sub(d):
                return {
                    "id": d["index"],
                    "name": d["name"],
                    "backend": d["hostapi"],
                    "sample_rate": d["default_samplerate"],
                    "max_channels": d["max_output_channels"],
                }
        return None

    def _pick_common_rate(
        self, in_idx: int, out_idx: int, dtype: str, ch_in: int, ch_out: int
    ) -> int | None:
        # Prefer device defaults if they match; then 48k, then 44.1k
        candidates = []
        try:
            rin = int(sd.query_devices(in_idx)["default_samplerate"])
            rout = int(sd.query_devices(out_idx)["default_samplerate"])
            if rin == rout:
                candidates.append(rin)
        except (sd.PortAudioError, KeyError, TypeError):
            pass
        for r in (self.TARGET_RATE, self.FALLBACK_RATE):
            if r not in candidates:
                candidates.append(r)

        for r in candidates:
            ok_in = ok_out = False
            try:
                sd.check_input_settings(device=in_idx, samplerate=r, channels=ch_in, dtype=dtype)
                ok_in = True
            except sd.PortAudioError:
                ok_in = False
            try:
                sd.check_output_settings(device=out_idx, samplerate=r, channels=ch_out, dtype=dtype)
                ok_out = True
            except sd.PortAudioError:
                ok_out = False
            logger.debug("Rate check %d Hz: IN=%s OUT=%s", r, ok_in, ok_out)
            if ok_in and ok_out:
                return r
        return None

    def _pick_best_input_for_hint(self, name_hint: str | None) -> dict | None:
        if not name_hint:
            return None
        all_devs = self._sd_list_devices()
        candidates = [
            d
            for d in all_devs
            if d["is_input"]
            and name_hint.lower() in d["name"].lower()
            and not self._is_blocklisted_input(d["name"])
        ]
        if not candidates:
            return None
        rank = {b: i for i, b in enumerate(self.PREFERRED_INPUT_BACKENDS)}
        candidates.sort(key=lambda d: (rank.get(d["hostapi"], 999), d["name"]))
        d = candidates[0]
        return {
            "id": d["index"],
            "name": d["name"],
            "backend": d["hostapi"],
            "max_channels": d["max_input_channels"],
            "default_samplerate": d["default_samplerate"],
        }
