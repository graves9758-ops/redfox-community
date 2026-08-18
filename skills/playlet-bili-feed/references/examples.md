# 使用示例

## 基础用法

### 生成最新日报
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --latest
```

### 生成指定日期日报
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --date 2026-06-10
```

## 自定义题材查询

### 穿越题材
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --topics "穿越,时空,重生"
```

### 霸总题材
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --topics "霸总,总裁,豪门,宠妻"
```

### 悬疑题材
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --topics "悬疑,推理,反转,惊悚"
```

### 多题材组合
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --topics "穿越,霸总,重生,悬疑"
```

## 订阅管理

### 开启订阅
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --subscribe
```

### 关闭订阅
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --unsubscribe
```

## 高级参数

### 自定义时间范围
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" \
  --start-time "2026-06-10 00:00:00" \
  --end-time "2026-06-10 23:59:59"
```

### 指定扫描数量
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --count 100
```

### 使用缓存数据
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --from-cache
```

### 指定输出目录
```bash
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --output-dir "/path/to/output"
```

## 常见场景

### 场景1:每日例行查询
```
用户:查询今天的短剧B站日报
Agent:检查日期→确认数据可用性→执行--latest
```

### 场景2:历史日期查询
```
用户:查询2026-06-10的短剧B站数据
Agent:直接执行--date 2026-06-10(历史数据已有)
```

### 场景3:未来日期查询
```
用户:查询明天的短剧B站数据
Agent:提示数据未更新→建议查询最新可用日期→等待确认
```

### 场景4:定向题材查询
```
用户:我想看穿越题材的短剧B站爆款
Agent:执行--topics "穿越,时空,重生"
```

## 输出示例

### 终端输出
```
## 短剧-B站信息源 · 2026-06-14 日报

**扫描 156 部热门短剧,聚类 8 个题材方向**

### 题材概览

| 题材 | 数量 | 占比 | 爆款亮点 |
|------|------|------|---------|
| #穿越 | 45部 | 28.8% | 《回到大明当王爷》12.3w赞 |
| #霸总 | 38部 | 24.4% | 《豪门替身妻》9.8w赞 |
| #重生 | 32部 | 20.5% | 《重生之逆袭人生》8.5w赞 |
| ... | ... | ... | ... |
```

### HTML日报
- 文件位置:`~/Downloads/QoderReports/短剧B站日报_2026-06-14.html`
- 自动浏览器打开
- 深色主题+B站蓝色主题色
- 卡片式布局+作品封面+互动数据
- 作品标题可点击跳转到B站视频
