def try_read_lid_angle():
    try:
        from pybooklid import read_lid_angle
        a = read_lid_angle()
        if a is None:
            return False, None
        return True, float(a)
    except Exception:
        return False, None
