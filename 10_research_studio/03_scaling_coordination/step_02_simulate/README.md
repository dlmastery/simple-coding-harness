# 10.10 · Simulate Leader-Follower Coordination

**Purpose:** See AReaL-RSI's conditional memory sharing in action.

## Simplified Simulation

```python
class LeaderAgent:
    def select_orientation(self, task):
        # Choose research direction based on task
        return orientation

class ResearcherAgent:
    def investigate(self, orientation):
        # Conduct experiments
        return findings

class ConditionalMemory:
    def store(self, finding, resolved):
        # Mark findings as resolved or unresolved
        pass
    
    def retrieve(self, orientation):
        # Return only relevant, resolved findings
        pass
```

## Your Task

Implement a simple 3-agent simulation (1 leader, 2 researchers) on a toy task.

## Next

[10.11 · Simulate swarm evolution](../step_03_swarm/README.md)
