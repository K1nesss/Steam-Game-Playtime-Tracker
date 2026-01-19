def format_playtime(seconds: int) -> str:
    """
    Format total seconds into a human-readable playtime string with abbreviated units (h/m/s).
    (将总秒数格式化为人类可读的游玩时长字符串，使用缩写单位时、分、秒)
    
    Rules for formatting (格式化规则):
    1. Hours are displayed first if greater than 0 (小时大于0时优先显示小时)
    2. Seconds are omitted if they are 0 (except for pure second values) (秒数为0时省略，纯秒数除外)
    3. Units use abbreviations: h (hours), m (minutes), s (seconds) (单位使用缩写：h=时，m=分，s=秒)
    
    Examples (示例):
    - 3661 seconds -> "1h1m1s"
    - 120 seconds -> "2m"
    - 45 seconds -> "45s"
    - 7200 seconds -> "2h0m" (will be formatted as "2h0m" (secs=0, so omitted))
    
    Args:
        seconds: Total playtime in seconds (游玩总时长，单位：秒)
        
    Returns:
        str: Formatted human-readable playtime string (格式化后的易读时长字符串)
    """
    # Validate input: must be a non-negative integer (验证输入：必须是非负整数)
    if not isinstance(seconds, int) or seconds < 0:
        return "0s"
    
    # Calculate hours, minutes and remaining seconds (计算小时、分钟和剩余秒数)
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    secs = remaining_seconds % 60
    
    # Format with hours (小时级格式：包含小时)
    if hours > 0:
        # Omit seconds if they are 0 (秒数为0时省略秒)
        if secs == 0:
            return f"{hours}h{minutes}m"
        return f"{hours}h{minutes}m{secs}s"
    # Format with minutes (no hours) (分钟级格式：无小时，仅包含分钟)
    elif minutes > 0:
        # Omit seconds if they are 0 (秒数为0时省略秒，仅显示分钟)
        if secs == 0:
            return f"{minutes}m"
        return f"{minutes}m{secs}s"
    # Format with only seconds (纯秒数格式：无小时和分钟)
    else:
        return f"{secs}s"