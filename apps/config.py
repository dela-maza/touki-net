### apps/config.py
config_data = [
  ['項目1', 10000, 2000],
  ['項目2', 10000, 2000],
  ['項目3', 10000, 2000],
]

# 起動時に変換
item_types = [row[0] for row in config_data]
reward_amounts = [row[1] for row in config_data]
expense_amounts = [row[2] for row in config_data]

config = {
  "item_types": item_types,
  "reward_amounts": reward_amounts,
  "expense_amounts": expense_amounts,
}

### apps/config.py
config_data = [
  ['項目A', 100000, 20000],
  ['項目B', 100000, 20000],
  ['項目C', 100000, 20000],
]

# 起動時に変換
item_types = [row[0] for row in config_data]
reward_amounts = [row[1] for row in config_data]
expense_amounts = [row[2] for row in config_data]

config = {
  "item_types": item_types,
  "reward_amounts": reward_amounts,
  "expense_amounts": expense_amounts,
}