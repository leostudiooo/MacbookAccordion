import pygame


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

WHITE_Q = [(pygame.K_q, 60), (pygame.K_w, 62), (pygame.K_e, 64), (pygame.K_r, 65), (pygame.K_t, 67),
           (pygame.K_y, 69), (pygame.K_u, 71), (pygame.K_i, 72), (pygame.K_o, 74), (pygame.K_p, 76)]
BLACK_1 = [(pygame.K_1, 61), (pygame.K_2, 63), (pygame.K_4, 66), (pygame.K_5, 68), (pygame.K_6, 70),
           (pygame.K_8, 73), (pygame.K_9, 75), (pygame.K_0, 78)]
WHITE_Z = [(pygame.K_z, 72), (pygame.K_x, 74), (pygame.K_c, 76), (pygame.K_v, 77), (pygame.K_b, 79),
           (pygame.K_n, 81), (pygame.K_m, 83), (pygame.K_COMMA, 84), (pygame.K_PERIOD, 86), (pygame.K_SLASH, 88)]
BLACK_A = [(pygame.K_a, 73), (pygame.K_s, 75), (pygame.K_d, 78), (pygame.K_f, 80), (pygame.K_g, 82),
           (pygame.K_h, 85), (pygame.K_j, 87), (pygame.K_k, 90), (pygame.K_l, 92), (pygame.K_SEMICOLON, 94)]
KEY_TO_MIDI = {k: m for k, m in (WHITE_Q + BLACK_1 + WHITE_Z + BLACK_A)}


def midi_to_name(m: int) -> str:
    m = int(max(0, min(127, m)))
    n = NOTE_NAMES[m % 12]
    o = (m // 12) - 1
    return f"{n}{o}"


def voice_key(kconst: int) -> str:
    return f"K_{kconst}"
