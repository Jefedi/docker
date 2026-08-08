# Data Table Upsert Pattern

Using the **Data Table** node with `operation: 'upsert'` to update existing rows or insert new ones — key for daily-sync workflows.

## Required Parameters

```javascript
matchType: 'allConditions',
filters: {
  conditions: [
    { keyName: 'playlist_id', condition: 'eq', keyValue: expr('{{ $json.playlist_id }}') }
  ]
}
```

- `matchType`: `'allConditions'` (all must match) or `'anyCondition'` (any one)
- `condition`: typically `'eq'`, loaded dynamically per column type
- Compound keys: add multiple condition entries

## Resource Mapper

```javascript
columns: {
  mappingMode: 'defineBelow',
  value: {
    col_a: expr('{{ $json.col_a }}'),
    col_b: expr('{{ $json.col_b }}')
  },
  schema: [
    { id: 'col_a', displayName: 'col_a', required: false, defaultMatch: true, display: true, type: 'string', canBeUsedToMatch: true },
    { id: 'col_b', displayName: 'col_b', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: false }
  ]
}
```

Key field props:
- `canBeUsedToMatch: true` — marks column for dedup matching
- `defaultMatch: true` — pre-selected in UI
- `type`: `'string'`, `'number'`, `'boolean'`, `'date'` — must match table schema

## Upsert vs Insert

| Operation | Use case |
|---|---|
| `insert` | Append-only logs, no duplicate concerns |
| `upsert` | Daily sync where data changes over time |
