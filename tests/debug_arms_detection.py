def _detect_arms_crossed(
    self,
    left_wrist: Landmark,
    right_wrist: Landmark,
    left_shoulder: Landmark,
    right_shoulder: Landmark,
    left_hip: Landmark,
    right_hip: Landmark
) -> bool:
    """
    Robust arms-crossed detection using spatial relationships.
    """

    # Visibility check
    if (
        left_wrist.visibility < 0.5 or
        right_wrist.visibility < 0.5 or
        left_shoulder.visibility < 0.5 or
        right_shoulder.visibility < 0.5
    ):
        return False

    # Shoulder center
    shoulder_cx = (left_shoulder.x + right_shoulder.x) / 2.0
    shoulder_cy = (left_shoulder.y + right_shoulder.y) / 2.0

    # Hip Y (for vertical validation)
    hip_y = (left_hip.y + right_hip.y) / 2.0

    # Distance helpers
    def dist(a: Landmark, b: Landmark) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    # Distances to opposite shoulders (key signal)
    lw_to_rs = dist(left_wrist, right_shoulder)
    rw_to_ls = dist(right_wrist, left_shoulder)

    # Distances to same-side shoulders
    lw_to_ls = dist(left_wrist, left_shoulder)
    rw_to_rs = dist(right_wrist, right_shoulder)

    # Wrists close to chest
    lw_center_dist = math.hypot(left_wrist.x - shoulder_cx, left_wrist.y - shoulder_cy)
    rw_center_dist = math.hypot(right_wrist.x - shoulder_cx, right_wrist.y - shoulder_cy)

    wrists_inward = (lw_center_dist < 0.25 and rw_center_dist < 0.25)

    # Wrists above hips (prevents relaxed hand false positives)
    wrists_up = (
        left_wrist.y < hip_y and
        right_wrist.y < hip_y
    )

    # Core crossed-arm condition
    crossed = (
        lw_to_rs < lw_to_ls and
        rw_to_ls < rw_to_rs and
        wrists_inward and
        wrists_up
    )

    return crossed
