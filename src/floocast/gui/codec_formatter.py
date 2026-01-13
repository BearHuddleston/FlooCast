"""Codec display formatting for audio codec information."""

RSSI_OFFSET = 0x100
APTX_ADAPTIVE_CODEC = 6
APTX_LOSSLESS_CODEC = 10


class CodecDisplayFormatter:
    def __init__(self, codec_strings, translate_func):
        self._codec_strings = codec_strings
        self._translate = translate_func

    def _codec_name(self, codec):
        if codec < len(self._codec_strings):
            return self._codec_strings[codec]
        return self._translate("Unknown")

    def _is_valid_codec(self, codec: int) -> bool:
        return 0 <= codec < len(self._codec_strings)

    def _is_aptx_codec(self, codec):
        return codec in (APTX_ADAPTIVE_CODEC, APTX_LOSSLESS_CODEC)

    def _format_rssi(self, rssi):
        return self._translate("RSSI") + " -" + str(RSSI_OFFSET - rssi) + "dBm"

    def _format_sample_rate(self, rate_hz):
        return str(float(rate_hz / 1000)) + "kHz"

    def _format_delay(self, delay):
        return str(float(delay) / 100) + "ms"

    def format(
        self,
        codec,
        rssi,
        rate,
        spk_sample_rate,
        mic_sample_rate,
        sdu_int,
        transport_delay,
        present_delay,
    ):
        codec_name = self._codec_name(codec)

        if transport_delay != 0:
            if self._is_aptx_codec(codec) and rssi != 0:
                if spk_sample_rate == 0:
                    return (
                        codec_name
                        + " @ "
                        + str(rate)
                        + "Kbps "
                        + self._format_delay(transport_delay)
                        + ", "
                        + self._format_rssi(rssi)
                    )
                return (
                    codec_name
                    + " @ "
                    + self._format_sample_rate(spk_sample_rate)
                    + " "
                    + str(rate)
                    + "Kbps "
                    + self._format_delay(transport_delay)
                    + ", "
                    + self._format_rssi(rssi)
                )
            if present_delay != 0:
                if mic_sample_rate != 0:
                    if not self._is_valid_codec(codec):
                        return self._translate("Unknown")
                    return (
                        codec_name
                        + " @ "
                        + str(float(spk_sample_rate / 1000))
                        + "|"
                        + str(float(mic_sample_rate / 1000))
                        + "kHz "
                        + self._format_delay(sdu_int)
                        + "+"
                        + self._format_delay(transport_delay)
                        + "+"
                        + self._format_delay(present_delay)
                    )
                if not self._is_valid_codec(codec):
                    return self._translate("Unknown")
                return (
                    codec_name
                    + " @ "
                    + self._format_sample_rate(spk_sample_rate)
                    + " "
                    + self._format_delay(sdu_int)
                    + "+"
                    + self._format_delay(transport_delay)
                    + "+"
                    + self._format_delay(present_delay)
                )
            return (
                codec_name
                + " @ "
                + self._format_sample_rate(spk_sample_rate)
                + " "
                + self._format_delay(transport_delay)
            )

        if self._is_aptx_codec(codec) and rssi != 0:
            if spk_sample_rate == 0:
                return codec_name + " @ " + str(rate) + "Kbps " + self._format_rssi(rssi)
            return (
                codec_name
                + " @ "
                + self._format_sample_rate(spk_sample_rate)
                + " "
                + str(rate)
                + "Kbps "
                + self._format_rssi(rssi)
            )

        if spk_sample_rate != 0 and mic_sample_rate != 0:
            if not self._is_valid_codec(codec):
                return self._translate("Unknown")
            return (
                codec_name
                + " @ "
                + str(float(spk_sample_rate / 1000))
                + "|"
                + str(float(mic_sample_rate / 1000))
                + "KHz"
            )

        if spk_sample_rate != 0:
            if not self._is_valid_codec(codec):
                return self._translate("Unknown")
            return codec_name + " @ " + str(float(spk_sample_rate / 1000)) + "KHz"

        if mic_sample_rate != 0:
            if not self._is_valid_codec(codec):
                return self._translate("Unknown")
            return codec_name + " @ 0| " + str(float(mic_sample_rate / 1000)) + "KHz"

        return codec_name
