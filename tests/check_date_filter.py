from datetime import datetime, timedelta

# Check the current time and calculate what the cutoff would be for different days values
now = datetime.now()
print(f"Current time: {now}")

for days in [30, 365, 0]:
    if days > 0:
        cutoff = now - timedelta(days=days)
        print(f"Days={days}: Cutoff date = {cutoff.isoformat()}")
    else:
        print(f"Days={days}: No cutoff (all time)")

# The target brain dump timestamp
target_timestamp = "2025-07-22T20:09:55.413468+00:00"
target_dt = datetime.fromisoformat(target_timestamp.replace('+00:00', ''))
print(f"\nTarget brain dump timestamp: {target_dt}")

# Check if it would be included
for days in [30, 365]:
    cutoff = now - timedelta(days=days)
    included = target_dt >= cutoff
    print(f"Days={days}: Would include target? {included} (cutoff: {cutoff})")
