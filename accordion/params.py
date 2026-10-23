from dataclasses import dataclass


@dataclass
class Param:
    key: str
    label: str
    value: float
    minv: float
    maxv: float
    step: float
    fmt: str
    group: str

    def clamp(self):
        if self.value < self.minv:
            self.value = self.minv
        if self.value > self.maxv:
            self.value = self.maxv
