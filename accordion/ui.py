import pygame

from .params import Param


class Slider:
    def __init__(self, param: Param, x, y, w=360, h=18):
        self.p = param
        self.base_y = y
        self.rect = pygame.Rect(x, y, w, h)
        self.drag = False

    def set_base_pos(self, x, y, w=None, h=None):
        self.rect.x = x
        self.base_y = y
        if w is not None:
            self.rect.w = w
        if h is not None:
            self.rect.h = h

    def apply_scroll(self, scroll_y: int):
        self.rect.y = self.base_y + scroll_y

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.drag = True
                self._set_from_mouse(e.pos[0])
                return True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = False
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self._set_from_mouse(e.pos[0])
            return True
        return False

    def _set_from_mouse(self, mx):
        t = (mx - self.rect.x) / max(1, self.rect.w)
        t = max(0.0, min(1.0, t))
        v = self.p.minv + t * (self.p.maxv - self.p.minv)
        if self.p.step > 0:
            v = round(v / self.p.step) * self.p.step
        self.p.value = float(v)
        self.p.clamp()

    def draw(self, screen, font, clip_rect: pygame.Rect):
        if not self.rect.colliderect(clip_rect):
            return
        pygame.draw.rect(screen, (65, 65, 75), self.rect, border_radius=6)
        t = (self.p.value - self.p.minv) / (self.p.maxv - self.p.minv) if self.p.maxv > self.p.minv else 0.0
        fillw = int(self.rect.w * max(0.0, min(1.0, t)))
        if fillw > 0:
            pygame.draw.rect(screen, (225, 225, 235), pygame.Rect(self.rect.x, self.rect.y, fillw, self.rect.h), border_radius=6)
        kx = self.rect.x + fillw
        pygame.draw.circle(screen, (245, 245, 245), (kx, self.rect.y + self.rect.h // 2), 8)
        label = f"{self.p.label}: {format(self.p.value, self.p.fmt)}"
        screen.blit(font.render(label, True, (220, 220, 220)), (self.rect.x + self.rect.w + 12, self.rect.y - 2))


class ScrollBar:
    def __init__(self):
        self.drag = False
        self.grab_off = 0

    def handle_event(self, e, bar_rect: pygame.Rect, knob_rect: pygame.Rect):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if knob_rect.collidepoint(e.pos):
                self.drag = True
                self.grab_off = e.pos[1] - knob_rect.y
                return True
            if bar_rect.collidepoint(e.pos):
                return "jump"
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = False
        elif e.type == pygame.MOUSEMOTION and self.drag:
            return "drag"
        return False
