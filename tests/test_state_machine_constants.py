from floocast.protocol.state_machine import BroadcastModeBit, FeatureBit, SourceState


class TestSourceStateConstants:
    def test_idle(self):
        assert SourceState.IDLE == 1

    def test_streaming_start(self):
        assert SourceState.STREAMING_START == 4

    def test_streaming(self):
        assert SourceState.STREAMING == 6


class TestFeatureBitConstants:
    def test_led(self):
        assert FeatureBit.LED == 0x01

    def test_aptx_lossless(self):
        assert FeatureBit.APTX_LOSSLESS == 0x02

    def test_gatt_client(self):
        assert FeatureBit.GATT_CLIENT == 0x04

    def test_audio_source(self):
        assert FeatureBit.AUDIO_SOURCE == 0x08

    def test_bits_are_unique(self):
        bits = [
            FeatureBit.LED,
            FeatureBit.APTX_LOSSLESS,
            FeatureBit.GATT_CLIENT,
            FeatureBit.AUDIO_SOURCE,
        ]
        assert len(bits) == len(set(bits))

    def test_bits_are_powers_of_two(self):
        for bit in [
            FeatureBit.LED,
            FeatureBit.APTX_LOSSLESS,
            FeatureBit.GATT_CLIENT,
            FeatureBit.AUDIO_SOURCE,
        ]:
            assert bit & (bit - 1) == 0


class TestBroadcastModeBitConstants:
    def test_encrypt(self):
        assert BroadcastModeBit.ENCRYPT == 0x01

    def test_public(self):
        assert BroadcastModeBit.PUBLIC == 0x02

    def test_high_quality(self):
        assert BroadcastModeBit.HIGH_QUALITY == 0x04

    def test_stop_on_idle(self):
        assert BroadcastModeBit.STOP_ON_IDLE == 0x08

    def test_latency_mask(self):
        assert BroadcastModeBit.LATENCY_MASK == 0x30

    def test_latency_shift(self):
        assert BroadcastModeBit.LATENCY_SHIFT == 4

    def test_flags_mask(self):
        assert BroadcastModeBit.FLAGS_MASK == 0x0F

    def test_all_mask(self):
        assert BroadcastModeBit.ALL_MASK == 0x3F

    def test_flag_bits_are_unique(self):
        bits = [
            BroadcastModeBit.ENCRYPT,
            BroadcastModeBit.PUBLIC,
            BroadcastModeBit.HIGH_QUALITY,
            BroadcastModeBit.STOP_ON_IDLE,
        ]
        assert len(bits) == len(set(bits))

    def test_flag_bits_are_powers_of_two(self):
        for bit in [
            BroadcastModeBit.ENCRYPT,
            BroadcastModeBit.PUBLIC,
            BroadcastModeBit.HIGH_QUALITY,
            BroadcastModeBit.STOP_ON_IDLE,
        ]:
            assert bit & (bit - 1) == 0

    def test_flags_mask_covers_all_flags(self):
        all_flags = (
            BroadcastModeBit.ENCRYPT
            | BroadcastModeBit.PUBLIC
            | BroadcastModeBit.HIGH_QUALITY
            | BroadcastModeBit.STOP_ON_IDLE
        )
        assert all_flags == BroadcastModeBit.FLAGS_MASK

    def test_latency_mask_is_upper_bits(self):
        assert BroadcastModeBit.LATENCY_MASK >> BroadcastModeBit.LATENCY_SHIFT == 0x03

    def test_all_mask_covers_flags_and_latency(self):
        assert (
            BroadcastModeBit.ALL_MASK == BroadcastModeBit.FLAGS_MASK | BroadcastModeBit.LATENCY_MASK
        )


class TestBroadcastModeBitOperations:
    def test_set_public_broadcast(self):
        mode = 0x00
        mode = (
            mode & ~BroadcastModeBit.PUBLIC & BroadcastModeBit.ALL_MASK
        ) | BroadcastModeBit.PUBLIC
        assert mode == 0x02

    def test_clear_public_broadcast(self):
        mode = 0x02
        mode = (mode & ~BroadcastModeBit.PUBLIC & BroadcastModeBit.ALL_MASK) | 0
        assert mode == 0x00

    def test_set_multiple_flags(self):
        mode = 0x00
        mode |= BroadcastModeBit.PUBLIC
        mode |= BroadcastModeBit.ENCRYPT
        mode |= BroadcastModeBit.HIGH_QUALITY
        assert mode == 0x07

    def test_set_latency_mode(self):
        mode = 0x00
        latency = 2
        mode = (mode & BroadcastModeBit.FLAGS_MASK) | (latency << BroadcastModeBit.LATENCY_SHIFT)
        assert mode == 0x20

    def test_get_latency_mode(self):
        mode = 0x25
        latency = (mode & BroadcastModeBit.LATENCY_MASK) >> BroadcastModeBit.LATENCY_SHIFT
        assert latency == 2

    def test_preserve_flags_when_setting_latency(self):
        mode = BroadcastModeBit.PUBLIC | BroadcastModeBit.ENCRYPT
        latency = 1
        mode = (mode & BroadcastModeBit.FLAGS_MASK) | (latency << BroadcastModeBit.LATENCY_SHIFT)
        assert mode == 0x13
        assert mode & BroadcastModeBit.PUBLIC != 0
        assert mode & BroadcastModeBit.ENCRYPT != 0

    def test_preserve_latency_when_setting_flag(self):
        mode = 2 << BroadcastModeBit.LATENCY_SHIFT
        mode = (
            mode & ~BroadcastModeBit.PUBLIC & BroadcastModeBit.ALL_MASK
        ) | BroadcastModeBit.PUBLIC
        assert (mode & BroadcastModeBit.LATENCY_MASK) >> BroadcastModeBit.LATENCY_SHIFT == 2
        assert mode & BroadcastModeBit.PUBLIC != 0
