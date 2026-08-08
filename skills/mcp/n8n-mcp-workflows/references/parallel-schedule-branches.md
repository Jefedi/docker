# Parallel Branches From One Schedule Trigger (SDK)

Multiple independent execution chains from a single `scheduleTrigger` — each branch runs its own sequence in parallel when the trigger fires.

## The Pattern

```javascript
const trigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Daily Schedule',
    parameters: {
      rule: {
        interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 8, triggerAtMinute: 0 }]
      }
    }
  },
  output: [{}]
});

const branchA = node({ ... });
const branchB = node({ ... });
const branchC = node({ ... });

export default workflow('id', 'name')
  .add(trigger).to(branchA)
  .add(trigger).to(branchB)
  .add(trigger).to(branchC);
```

Each `.add(trigger).to(...)` creates a separate execution path. All run simultaneously.

## Why Not Chain?

❌ **Wrong**: `.to(branchA).to(branchB)` — sequential; branchB waits for branchA and receives its items.
✅ **Correct**: Parallel `.add(trigger).to(branchA)` then `.add(trigger).to(branchB)`.

## Caveats

- Sections start above the first `.add()` call — the `workflow(...)` call begins the chain
- Within each branch, normal linear chaining applies: `.to(fetch).to(transform).to(store)`
- For loops within a branch, use `splitInBatches` inside the chain:
  ```javascript
  .add(trigger).to(fetchList).to(splitInBatches({ version: 3, config: { parameters: { batchSize: 1 } } })
    .onEachBatch(processItem.to(nextBatch(sib)))
    .onDone(noOp)
  )
  ```
- No `Merge` node needed unless you must combine streams downstream
