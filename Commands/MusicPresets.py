import wavelink
from typing import Dict

class MusicPreset:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.filters = wavelink.Filters()

    async def apply(self, player: wavelink.Player):
        await player.set_filters(self.filters)
        setattr(player, "current_preset", self.name)

class PresetManager:
    def __init__(self):
        self.presets: Dict[str, MusicPreset] = {}
        self._initialize_presets()

    def _initialize_presets(self):
        # Bass Boost Preset
        bass_boost = MusicPreset("Bass Boost", "Enhanced bass frequencies")
        bass_boost.filters.equalizer.set(0, 0.6)
        bass_boost.filters.equalizer.set(1, 0.4)
        self.presets["bass"] = bass_boost

        # Nightcore Preset
        nightcore = MusicPreset("Nightcore", "Increased speed and pitch")
        nightcore.filters.timescale.set(speed=1.2, pitch=1.2)
        self.presets["nightcore"] = nightcore

        # 8D Audio Preset
        eight_d = MusicPreset("8D", "Rotating audio effect")
        eight_d.filters.rotation.set(rotation_hz=0.2)
        self.presets["8d"] = eight_d

        # Pop Preset
        pop = MusicPreset("Pop", "Enhanced vocals and mid frequencies")
        pop.filters.equalizer.set(0, -0.1)  # Reduce bass
        pop.filters.equalizer.set(4, 0.3)   # Boost mids
        pop.filters.equalizer.set(7, 0.2)   # Boost highs
        self.presets["pop"] = pop

        # Rock Preset
        rock = MusicPreset("Rock", "Enhanced guitar frequencies")
        rock.filters.equalizer.set(0, 0.3)   # Bass
        rock.filters.equalizer.set(3, 0.2)   # Low mids
        rock.filters.equalizer.set(5, 0.2)   # High mids
        self.presets["rock"] = rock

        # Classical Preset
        classical = MusicPreset("Classical", "Natural frequency balance")
        classical.filters.equalizer.set(0, -0.1)  # Slight bass reduction
        classical.filters.equalizer.set(6, 0.1)   # Slight treble boost
        self.presets["classical"] = classical

    def get_preset(self, name: str) -> MusicPreset:
        return self.presets.get(name.lower())

    def get_preset_names(self) -> list[str]:
        return list(self.presets.keys())

    def get_preset_descriptions(self) -> Dict[str, str]:
        return {name: preset.description for name, preset in self.presets.items()}

async def setup(bot):
    # This cog doesn't need any setup as it's just a utility class
    pass