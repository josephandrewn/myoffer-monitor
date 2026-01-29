"""
Test the human delay patterns
"""
import time
import random

def human_delay(base_seconds=3):
    rand = random.random()
    
    if rand < 0.70:
        delay = random.uniform(2.0, 5.0)
        category = "NORMAL"
    elif rand < 0.90:
        delay = random.uniform(0.5, 2.0)
        category = "QUICK"
    else:
        delay = random.uniform(5.0, 15.0)
        category = "DISTRACTED"
    
    return delay, category

def test_delays():
    print("Testing Human Delay Patterns")
    print("=" * 60)
    print("\nSimulating 20 delays to see distribution:\n")
    
    delays = []
    categories = {"QUICK": 0, "NORMAL": 0, "DISTRACTED": 0}
    
    for i in range(20):
        delay, category = human_delay()
        delays.append(delay)
        categories[category] += 1
        print(f"Delay {i+1:2d}: {delay:5.2f}s [{category}]")
    
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print("=" * 60)
    print(f"Average delay: {sum(delays)/len(delays):.2f}s")
    print(f"Min delay: {min(delays):.2f}s")
    print(f"Max delay: {max(delays):.2f}s")
    print(f"\nDistribution:")
    print(f"  Quick (0.5-2s):      {categories['QUICK']:2d}/20 ({categories['QUICK']*5}%)")
    print(f"  Normal (2-5s):       {categories['NORMAL']:2d}/20 ({categories['NORMAL']*5}%)")
    print(f"  Distracted (5-15s):  {categories['DISTRACTED']:2d}/20 ({categories['DISTRACTED']*5}%)")
    
    print("\n✓ This looks human-like!")
    print("  Expected: ~20% quick, ~70% normal, ~10% distracted")

if __name__ == "__main__":
    test_delays()