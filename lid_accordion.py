\
#!/usr/bin/env python3
import math
import sys
import time
import pygame

from accordion.audio import BLOCK_SIZE, SAMPLE_RATE, TONE_NAMES, PolyAccordionSynth
from accordion.input import try_read_lid_angle
from accordion.keyboard import KEY_TO_MIDI, midi_to_name, voice_key
from accordion.params import Param
from accordion.ui import ScrollBar, Slider, ToneSelector
import sounddevice as sd

def clamp(v, a, b):
    return a if v < a else b if v > b else v

def main():
    pygame.init()
    W, H = 1320, 780
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("Lid Accordion - Fix21 (scroll clipped below header)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    font_big = pygame.font.SysFont(None, 42)

    RESERVED_FOOTER_H = 92
    SCROLLBAR_W = 14
    SCROLL_STEP = 42
    SCROLL_AREA_TOP = 332  # below fixed header

    synth = PolyAccordionSynth()
    held = {}
    octave_off = 0

    def clamp_oct(off: int) -> int:
        return max(-36, min(36, off))

    def retune_all():
        for _, (vk, base_midi) in held.items():
            synth.retune(vk, max(0, min(127, base_midi + octave_off)))

    ok, angle = try_read_lid_angle()
    simulated = not ok
    angle_sim = 45.0
    prev_angle = angle if ok else angle_sim
    prev_t = time.time()

    params = [
        Param("vel_max",   "Bellows sensitivity",     160.0, 30.0, 400.0, 1.0,  ".0f", "Bellows"),
        Param("deadzone",  "Ignore tiny movement",    0.010, 0.000, 0.080, 0.001, ".3f", "Bellows"),
        Param("fill_rate", "How fast air builds",     2.2,   0.1,  8.0,   0.1,  ".1f", "Bellows"),
        Param("leak_rate", "How fast air leaks",      0.12,  0.00, 2.0,   0.01, ".2f", "Bellows"),
        Param("rise_a",    "Volume rise smoothness",  0.70,  0.00, 0.99,  0.01, ".2f", "Bellows"),
        Param("fall_a",    "Volume fall smoothness",  0.96,  0.00, 0.999, 0.001,".3f", "Bellows"),
        Param("master",    "Overall volume",          synth.master, 0.05, 1.20, 0.01, ".2f", "Sound"),
        Param("attack_s",  "Note attack time (s)",    synth.attack, 0.001,0.200,0.001,".3f", "Sound"),
        Param("release_s", "Note release time (s)",   synth.release,0.010,1.000,0.005,".3f", "Sound"),
        Param("detune",    "Reed thickness (detune)", synth.detune, 0.000,0.050,0.001,".3f", "Sound"),
        Param("noise",     "Air / reed noise",        synth.noise_amount,0.000,0.080,0.001,".3f", "Sound"),
        Param("filter_cutoff", "Reed filter cutoff",  synth.filter_cutoff, 0.10, 1.00, 0.01, ".2f", "Sound"),
        Param("filter_resonance", "Filter resonance", synth.filter_resonance, 0.00, 0.15, 0.01, ".2f", "Sound"),
        Param("chorus_mix", "Chorus mix",             synth.chorus_mix, 0.00, 0.40, 0.01, ".2f", "Sound"),
        Param("chorus_rate", "Chorus rate (Hz)",       synth.chorus_rate, 0.10, 1.50, 0.01, ".2f", "Sound"),
    ]
    by_key = {p.key: p for p in params}

    def apply_synth_params():
        synth.master = by_key["master"].value
        synth.attack = by_key["attack_s"].value
        synth.release = by_key["release_s"].value
        synth.detune = by_key["detune"].value
        synth.noise_amount = by_key["noise"].value
        synth.filter_cutoff = by_key["filter_cutoff"].value
        synth.filter_resonance = by_key["filter_resonance"].value
        synth.chorus_mix = by_key["chorus_mix"].value
        synth.chorus_rate = by_key["chorus_rate"].value

    sliders = [Slider(p, 0, 0, w=420, h=18) for p in params]
    scrollbar = ScrollBar()
    tone_selector = ToneSelector(TONE_NAMES, synth.tone)

    scroll_y = 0
    content_h = 0

    def layout(win_w, win_h):
        nonlocal content_h, scroll_y
        sx = 26
        base_y = 360
        line_h = 30
        slider_w = max(260, min(600, win_w - 26 - 26 - 340 - SCROLLBAR_W))
        groups = ["Bellows", "Sound"]
        y = base_y
        idx = 0
        for g in groups:
            y += 26
            for p in [pp for pp in params if pp.group == g]:
                sliders[idx].set_base_pos(sx, y, w=slider_w, h=18)
                idx += 1
                y += line_h
            y += 38
        content_h = y + 20
        view_h = (win_h - RESERVED_FOOTER_H) - SCROLL_AREA_TOP
        max_down = min(0, view_h - content_h)
        scroll_y = clamp(scroll_y, max_down, 0)
        tone_selector.layout(22, 294, button_w=min(220, max(150, (win_w - 60) // max(1, len(TONE_NAMES)))), h=30)

    def apply_scroll():
        for s in sliders:
            s.apply_scroll(scroll_y)

    def set_scroll_from_ratio(r, win_h):
        nonlocal scroll_y
        view_h = (win_h - RESERVED_FOOTER_H) - SCROLL_AREA_TOP
        max_down = min(0, view_h - content_h)
        scroll_y = int(round(max_down * r))
        apply_scroll()

    layout(W, H)
    apply_scroll()

    air = 0.0
    bellows = 0.0

    audio_ok = True
    stream = None
    def audio_callback(outdata, frames, time_info, status):
        outdata[:] = synth.generate_frames(frames)

    try:
        stream = sd.OutputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, channels=2, dtype="float32", callback=audio_callback)
        stream.start()
    except Exception as e:
        audio_ok = False
        print("Failed to start audio OutputStream:", e)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        now = time.time()
        win_w, win_h = screen.get_size()

        apply_synth_params()

        view_h = (win_h - RESERVED_FOOTER_H) - SCROLL_AREA_TOP
        max_scroll_down = min(0, view_h - content_h)
        scrollable = (content_h > view_h)

        bar_rect = pygame.Rect(win_w - SCROLLBAR_W - 6, SCROLL_AREA_TOP + 8, SCROLLBAR_W, max(50, view_h - 16))
        if scrollable:
            r = 0.0 if max_scroll_down == 0 else (scroll_y / max_scroll_down)
            r = clamp(r, 0.0, 1.0)
            knob_h = max(40, int(bar_rect.h * (view_h / content_h)))
            knob_y = int(bar_rect.y + (bar_rect.h - knob_h) * r)
            knob_rect = pygame.Rect(bar_rect.x, knob_y, bar_rect.w, knob_h)
        else:
            knob_rect = pygame.Rect(bar_rect.x, bar_rect.y, bar_rect.w, bar_rect.h)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                layout(event.w, event.h)
                apply_scroll()

            selected_tone = tone_selector.handle_event(event)
            if selected_tone is not None:
                synth.set_tone(selected_tone)

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if event.type != pygame.MOUSEMOTION:
                    mx, my = event.pos
                    if my >= win_h - RESERVED_FOOTER_H:
                        continue

            if scrollable:
                sb = scrollbar.handle_event(event, bar_rect, knob_rect)
                if sb:
                    if sb == "jump" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        click_y = event.pos[1]
                        t = (click_y - bar_rect.y) / max(1, bar_rect.h)
                        t = clamp(t, 0.0, 1.0)
                        set_scroll_from_ratio(t, win_h)
                    elif sb == "drag" and event.type == pygame.MOUSEMOTION:
                        ky = event.pos[1] - scrollbar.grab_off
                        t = (ky - bar_rect.y) / max(1, (bar_rect.h - knob_rect.h))
                        t = clamp(t, 0.0, 1.0)
                        set_scroll_from_ratio(t, win_h)
                    continue

            if event.type == pygame.MOUSEWHEEL and scrollable:
                mx, my = pygame.mouse.get_pos()
                if SCROLL_AREA_TOP <= my < win_h - RESERVED_FOOTER_H:
                    scroll_y = int(clamp(scroll_y + event.y * SCROLL_STEP, max_scroll_down, 0))
                    apply_scroll()
                    continue

            used = False
            for s in sliders:
                if s.handle_event(event):
                    used = True
            if used:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if simulated:
                    if event.key == pygame.K_UP: angle_sim = min(110.0, angle_sim + 3.0)
                    elif event.key == pygame.K_DOWN: angle_sim = max(0.0, angle_sim - 3.0)

                if event.key in KEY_TO_MIDI and event.key not in held:
                    base_midi = KEY_TO_MIDI[event.key]
                    vk = voice_key(event.key)
                    held[event.key] = (vk, base_midi)
                    synth.note_on(vk, max(0, min(127, base_midi + octave_off)))

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    octave_off = clamp_oct(octave_off + 12); retune_all()
                elif event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    octave_off = clamp_oct(octave_off - 12); retune_all()
                elif event.key == pygame.K_TAB:
                    octave_off = 0; retune_all()

                if event.key in held:
                    vk, _ = held.pop(event.key)
                    synth.note_off(vk)

        if not simulated:
            ok, a = try_read_lid_angle()
            if ok and a is not None: angle = a
            else: simulated = True; angle = angle_sim
        else:
            angle = angle_sim

        dt_vel = max(1e-6, now - prev_t)
        vel = (angle - prev_angle) / dt_vel
        prev_angle, prev_t = angle, now

        vel_max = by_key["vel_max"].value
        deadzone = by_key["deadzone"].value
        fill_rate = by_key["fill_rate"].value
        leak_rate = by_key["leak_rate"].value
        rise_a = by_key["rise_a"].value
        fall_a = by_key["fall_a"].value

        b_raw = min(1.0, abs(vel) / max(1e-6, vel_max))
        b_raw = 0.0 if b_raw < deadzone else b_raw

        air = max(0.0, min(1.0, air + (b_raw * fill_rate - leak_rate) * dt))
        target = air
        bellows = (bellows * rise_a + target * (1.0 - rise_a)) if target > bellows else (bellows * fall_a + target * (1.0 - fall_a))
        synth.set_bellows(bellows)

        # --- draw fixed header ---
        screen.fill((20, 20, 24))
        screen.blit(font_big.render("Live Tweak Panel", True, (240, 240, 240)), (22, 18))
        mode_text = "SIMULATED (↑↓ / wheel)" if simulated else "LIVE (Lid Angle Sensor)"
        screen.blit(font.render(f"Mode: {mode_text}", True, (200, 200, 200)), (22, 72))
        audio_text = "OK" if audio_ok else "FAILED (check Terminal / PortAudio)"
        screen.blit(font.render(f"Audio: {audio_text}", True, (200, 200, 200)), (22, 96))
        octave_txt = f"{octave_off//12:+d}" if octave_off != 0 else "0"
        screen.blit(font.render(f"Octave: {octave_txt}  (Shift key-up: +1 | Ctrl key-up: -1 | Tab: reset)", True, (220, 220, 220)), (22, 120))
        screen.blit(font.render(f"Angle: {angle:6.1f} deg", True, (220, 220, 220)), (22, 150))
        screen.blit(font.render(f"Vel:   {vel:7.1f} deg/s (push/pull both)", True, (220, 220, 220)), (22, 174))
        screen.blit(font.render(f"Bellows: {bellows:0.3f}   air: {air:0.3f}", True, (220, 220, 220)), (22, 198))
        held_notes = [midi_to_name(base + octave_off) for (_, base) in held.values()]
        screen.blit(font.render(f"Held notes: {', '.join(held_notes) if held_notes else '-'}", True, (220, 220, 220)), (22, 230))
        screen.blit(font.render("Tone:", True, (220, 220, 220)), (22, 294))
        tone_selector.draw(screen, font)
        bar_x, bar_y, bar_w, bar_h = 22, 264, min(720, win_w - 44 - SCROLLBAR_W - 10), 22
        pygame.draw.rect(screen, (70, 70, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        pygame.draw.rect(screen, (230, 230, 230), (bar_x, bar_y, int(bar_w * bellows), bar_h), border_radius=8)

        gx = min(win_w - 220 - SCROLLBAR_W, 740)
        gy = 190
        radius = 140
        pygame.draw.circle(screen, (60, 60, 70), (gx, gy), radius, width=4)
        ang_norm = (angle / 110.0)
        theta = math.radians(-120 + 240 * ang_norm)
        x2 = gx + int((radius - 10) * math.cos(theta))
        y2 = gy + int((radius - 10) * math.sin(theta))
        pygame.draw.line(screen, (240, 240, 240), (gx, gy), (x2, y2), width=6)
        pygame.draw.circle(screen, (240, 240, 240), (gx, gy), 8)

        pygame.draw.line(screen, (45, 45, 55), (0, SCROLL_AREA_TOP), (win_w, SCROLL_AREA_TOP), 2)

        # --- draw scrollable content, clipped below header ---
        clip_rect = pygame.Rect(0, SCROLL_AREA_TOP + 2, win_w, (win_h - RESERVED_FOOTER_H) - (SCROLL_AREA_TOP + 2))
        prev_clip = screen.get_clip()
        screen.set_clip(clip_rect)

        pygame.draw.line(screen, (45, 45, 55), (22, 340 + scroll_y), (win_w - 22 - SCROLLBAR_W - 8, 340 + scroll_y), 2)
        screen.blit(font_big.render("Bellows", True, (240, 240, 240)), (22, 350 + scroll_y))
        screen.blit(font_big.render("Sound", True, (240, 240, 240)), (22, 560 + scroll_y))

        for s in sliders:
            s.draw(screen, font, clip_rect)

        screen.set_clip(prev_clip)

        if scrollable:
            pygame.draw.rect(screen, (40, 40, 48), bar_rect, border_radius=8)
            pygame.draw.rect(screen, (215, 215, 225), knob_rect, border_radius=8)

        cheat1 = r"Keymap: Q2W3ER5T6Y7UI9O0P[= Backspace \ (C4 to G#5)"
        cheat2 = "High: ZSXDCVGBHNJM,L.;/ (C5 to E6) | Mouse wheel in param area to scroll"
        footer_y = win_h - RESERVED_FOOTER_H
        pygame.draw.rect(screen, (14, 14, 18), (0, footer_y, win_w, RESERVED_FOOTER_H))
        pygame.draw.line(screen, (45, 45, 55), (0, footer_y), (win_w, footer_y), 2)
        screen.blit(font.render(cheat1, True, (170, 170, 170)), (22, footer_y + 18))
        screen.blit(font.render(cheat2, True, (170, 170, 170)), (22, footer_y + 44))

        pygame.display.flip()

    try:
        if stream is not None:
            stream.stop()
            stream.close()
    except Exception:
        pass

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
