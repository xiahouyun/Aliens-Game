import core.constants as const
from core.data_manager import DataManager

print(f'Initial SCORE: {const.SCORE}')

dm = DataManager()
dm.load_save()
print(f'High score from save: {dm.save_data.get("high_score", 0)}')

# 修改分数测试
const.SCORE = 5
print(f'SCORE after change: {const.SCORE}')

# 更新最高分
dm.update_high_score(const.SCORE)
print(f'High score after update: {dm.save_data.get("high_score", 0)}')

# 重新加载检查保存
dm2 = DataManager()
dm2.load_save()
print(f'High score after reload: {dm2.save_data.get("high_score", 0)}')
