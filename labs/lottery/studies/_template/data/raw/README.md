# data/raw —— 原始数据（模板占位）

把**未经任何加工的原始开奖数据**放在这里。

## 硬要求

1. **只读**：放入后不得修改。任何清洗都产出到 `../derived/`。
2. **必须算 SHA256**，写进 `game.yaml` 的 `data.raw[].sha256`。
   校验器会实算比对，手填/抄错会直接失败。
3. **必须记录口径**：期号范围、起止日期、列名含义，写进 `game.yaml` 的 `data.columns`。
4. **发现缺口要写出来**：缺失的期、重复的期、口径变更的期，
   全部写进 `game.yaml` 的 `data.caveats`。**不要悄悄补齐。**

## 为什么这么严

历史教训：数据口径不明 → 拿"开出率"当"被选中率" → 整轮结论作废（见 `labs/lottery/studies/dlt/memory/lessons/LESSONS.md` L7）。
数据一旦被修改过，所有基于它的结论都不可复现。

## 算 SHA256

```bash
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" data/raw/xxx.csv
```
