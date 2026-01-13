from floocast.settings import FlooSettings


class TestFlooSettingsGetSet:
    def test_get_returns_default_for_missing_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        assert settings.get("nonexistent") is None
        assert settings.get("nonexistent", "default") == "default"

    def test_set_and_get_string(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("key", "value")
        assert settings.get("key") == "value"

    def test_set_and_get_int(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("count", 42)
        assert settings.get("count") == 42

    def test_set_and_get_bool(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("enabled", True)
        assert settings.get("enabled") is True

    def test_set_and_get_list(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("items", [1, 2, 3])
        assert settings.get("items") == [1, 2, 3]

    def test_update_multiple_keys(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.update({"a": 1, "b": 2})
        assert settings.get("a") == 1
        assert settings.get("b") == 2

    def test_remove_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("key", "value")
        settings.remove("key")
        assert settings.get("key") is None

    def test_remove_nonexistent_key_no_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.remove("nonexistent")


class TestFlooSettingsItemHelpers:
    def test_set_item_dict_creates_copy(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        original = {"name": "device1", "id": 123}
        settings.set_item("device", original)
        original["name"] = "modified"
        assert settings.get_item("device")["name"] == "device1"

    def test_get_item_dict_returns_copy(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set_item("device", {"name": "device1"})
        retrieved = settings.get_item("device")
        retrieved["name"] = "modified"
        assert settings.get_item("device")["name"] == "device1"

    def test_set_item_scalar(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set_item("start_minimized", True)
        assert settings.get_item("start_minimized") is True

    def test_get_item_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        assert settings.get_item("nonexistent") is None
        assert settings.get_item("nonexistent", {"default": True}) == {"default": True}


class TestFlooSettingsPersistence:
    def test_save_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        settings.set("key", "value")
        settings.save()
        assert (tmp_path / "FlooCast" / "settings.json").exists()

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings1 = FlooSettings()
        settings1.set("string", "hello")
        settings1.set("number", 42)
        settings1.set("bool", True)
        settings1.set_item("device", {"name": "test", "id": 1})
        settings1.save()

        settings2 = FlooSettings()
        assert settings2.get("string") == "hello"
        assert settings2.get("number") == 42
        assert settings2.get("bool") is True
        assert settings2.get_item("device") == {"name": "test", "id": 1}

    def test_load_handles_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        assert settings.get("anything") is None

    def test_load_handles_corrupt_json(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "FlooCast"
        config_dir.mkdir(parents=True)
        (config_dir / "settings.json").write_text("not valid json {{{")
        settings = FlooSettings()
        assert settings.get("anything") is None

    def test_load_handles_non_dict_json(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "FlooCast"
        config_dir.mkdir(parents=True)
        (config_dir / "settings.json").write_text('["array", "not", "dict"]')
        settings = FlooSettings()
        assert settings.get("anything") is None


class TestFlooSettingsPath:
    def test_default_path_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings()
        assert settings.path == tmp_path / "FlooCast" / "settings.json"

    def test_custom_app_name(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings(app_name="CustomApp")
        assert settings.path == tmp_path / "CustomApp" / "settings.json"

    def test_custom_filename(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        settings = FlooSettings(filename="config.json")
        assert settings.path == tmp_path / "FlooCast" / "config.json"
