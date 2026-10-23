import pygame


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

LOWER_KEYBOARD = [
    pygame.K_q, pygame.K_2, pygame.K_w, pygame.K_3, pygame.K_e, pygame.K_r, pygame.K_5,
    pygame.K_t, pygame.K_6, pygame.K_y, pygame.K_7, pygame.K_u, pygame.K_i, pygame.K_9,
    pygame.K_o, pygame.K_0, pygame.K_p, pygame.K_LEFTBRACKET, pygame.K_EQUALS,
    pygame.K_BACKSPACE, pygame.K_BACKSLASH,
]
UPPER_KEYBOARD = [
    pygame.K_z, pygame.K_s, pygame.K_x, pygame.K_d, pygame.K_c, pygame.K_v, pygame.K_g,
    pygame.K_b, pygame.K_h, pygame.K_n, pygame.K_j, pygame.K_m, pygame.K_COMMA,
    pygame.K_l, pygame.K_PERIOD, pygame.K_SEMICOLON, pygame.K_SLASH,
]
KEY_TO_MIDI = {
    key: midi
    for key, midi in (
        [(key, 60 + offset) for offset, key in enumerate(LOWER_KEYBOARD)]
        + [(key, 72 + offset) for offset, key in enumerate(UPPER_KEYBOARD)]
    )
}


def midi_to_name(m: int) -> str:
    m = int(max(0, min(127, m)))
    n = NOTE_NAMES[m % 12]
    o = (m // 12) - 1
    return f"{n}{o}"


def voice_key(kconst: int) -> str:
    return f"K_{kconst}"
