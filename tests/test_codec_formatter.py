import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "codec_formatter", Path(__file__).parent.parent / "src/floocast/gui/codec_formatter.py"
)
codec_formatter = importlib.util.module_from_spec(spec)
sys.modules["codec_formatter"] = codec_formatter
spec.loader.exec_module(codec_formatter)

APTX_ADAPTIVE_CODEC = codec_formatter.APTX_ADAPTIVE_CODEC
APTX_LOSSLESS_CODEC = codec_formatter.APTX_LOSSLESS_CODEC
RSSI_OFFSET = codec_formatter.RSSI_OFFSET
CodecDisplayFormatter = codec_formatter.CodecDisplayFormatter

CODEC_STRINGS = [
    "None",
    "CVSD",
    "mSBC/WBS",
    "SBC",
    "aptX",
    "aptX HD",
    "aptX Adaptive",
    "LC3",
    "aptX Adaptive",
    "aptX Lite",
    "aptX Lossless",
    "aptX Voice",
]


def identity(s):
    return s


class TestCodecFormatterConstants:
    def test_rssi_offset(self):
        assert RSSI_OFFSET == 0x100

    def test_aptx_adaptive_codec(self):
        assert APTX_ADAPTIVE_CODEC == 6

    def test_aptx_lossless_codec(self):
        assert APTX_LOSSLESS_CODEC == 10


class TestCodecFormatterHelpers:
    def test_codec_name_valid(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._codec_name(0) == "None"
        assert formatter._codec_name(3) == "SBC"
        assert formatter._codec_name(6) == "aptX Adaptive"

    def test_codec_name_invalid(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._codec_name(99) == "Unknown"

    def test_is_aptx_codec(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._is_aptx_codec(6) is True
        assert formatter._is_aptx_codec(10) is True
        assert formatter._is_aptx_codec(3) is False
        assert formatter._is_aptx_codec(7) is False

    def test_format_rssi(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._format_rssi(200) == "RSSI -56dBm"
        assert formatter._format_rssi(150) == "RSSI -106dBm"

    def test_format_sample_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._format_sample_rate(48000) == "48.0kHz"
        assert formatter._format_sample_rate(44100) == "44.1kHz"

    def test_format_delay(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        assert formatter._format_delay(1000) == "10.0ms"
        assert formatter._format_delay(250) == "2.5ms"


class TestCodecFormatterBasic:
    def test_codec_name_only(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=3,
            rssi=0,
            rate=0,
            spk_sample_rate=0,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "SBC"

    def test_unknown_codec(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=0,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "Unknown"


class TestCodecFormatterWithSpeakerSampleRate:
    def test_spk_sample_rate_only(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=3,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "SBC @ 48.0KHz"

    def test_spk_and_mic_sample_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=7,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=16000,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "LC3 @ 48.0|16.0KHz"

    def test_mic_sample_rate_only(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=7,
            rssi=0,
            rate=0,
            spk_sample_rate=0,
            mic_sample_rate=16000,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "LC3 @ 0| 16.0KHz"


class TestCodecFormatterWithTransportDelay:
    def test_transport_delay_with_spk_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=3,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=1000,
            present_delay=0,
        )
        assert result == "SBC @ 48.0kHz 10.0ms"

    def test_transport_delay_with_present_delay_spk_only(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=7,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=500,
            transport_delay=1000,
            present_delay=2000,
        )
        assert result == "LC3 @ 48.0kHz 5.0ms+10.0ms+20.0ms"

    def test_transport_delay_with_present_delay_and_mic(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=7,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=16000,
            sdu_int=500,
            transport_delay=1000,
            present_delay=2000,
        )
        assert result == "LC3 @ 48.0|16.0kHz 5.0ms+10.0ms+20.0ms"


class TestCodecFormatterAptX:
    def test_aptx_adaptive_with_rssi_no_spk_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=6,
            rssi=200,
            rate=320,
            spk_sample_rate=0,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "aptX Adaptive @ 320Kbps RSSI -56dBm"

    def test_aptx_adaptive_with_rssi_and_spk_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=6,
            rssi=200,
            rate=320,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "aptX Adaptive @ 48.0kHz 320Kbps RSSI -56dBm"

    def test_aptx_lossless_with_rssi(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=10,
            rssi=180,
            rate=1200,
            spk_sample_rate=96000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "aptX Lossless @ 96.0kHz 1200Kbps RSSI -76dBm"

    def test_aptx_with_transport_delay_and_rssi_no_spk(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=6,
            rssi=200,
            rate=320,
            spk_sample_rate=0,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=1000,
            present_delay=0,
        )
        assert result == "aptX Adaptive @ 320Kbps 10.0ms, RSSI -56dBm"

    def test_aptx_with_transport_delay_and_rssi_with_spk(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=6,
            rssi=200,
            rate=320,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=1000,
            present_delay=0,
        )
        assert result == "aptX Adaptive @ 48.0kHz 320Kbps 10.0ms, RSSI -56dBm"


class TestCodecFormatterUnknownCodecBranches:
    def test_unknown_with_spk_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "Unknown"

    def test_unknown_with_mic_rate(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=0,
            mic_sample_rate=16000,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "Unknown"

    def test_unknown_with_both_rates(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=16000,
            sdu_int=0,
            transport_delay=0,
            present_delay=0,
        )
        assert result == "Unknown"

    def test_unknown_with_transport_and_present_delay(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=16000,
            sdu_int=500,
            transport_delay=1000,
            present_delay=2000,
        )
        assert result == "Unknown"

    def test_unknown_with_transport_present_delay_no_mic(self):
        formatter = CodecDisplayFormatter(CODEC_STRINGS, identity)
        result = formatter.format(
            codec=99,
            rssi=0,
            rate=0,
            spk_sample_rate=48000,
            mic_sample_rate=0,
            sdu_int=500,
            transport_delay=1000,
            present_delay=2000,
        )
        assert result == "Unknown"
