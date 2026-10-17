<div align="center">

# 🧭 build-next

**下个项目做什么 —— 用「需求减供给」算，不靠拍脑袋。**
读实时 GitHub 热榜和技能注册表搜索，把「注意力在涨、但供给还很薄」的缝隙排出来。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![零依赖](https://img.shields.io/badge/运行时依赖-0-brightgreen)](pyproject.toml)
[![不需要 LLM](https://img.shields.io/badge/LLM-不需要-success)]()

[English](README.md) · [简体中文](README.zh-CN.md)

**在线扫描 →** [中文](https://weiwei0614.github.io/build-next/) · [English](https://weiwei0614.github.io/build-next/en.html)

</div>

---

## 「做什么项目」这件事的问题在哪

问十个人得十个答案，且都受他们上周刚好刷到什么影响。这个工具把那句话换成两个你自己能重测的数字：

```
机会 ≈ 需求（热榜实测的注意力） − 供给（仓库数与注册表命中实测的拥挤度）
```

## 它实际扫出来的东西

2026-10-17 的一次真实运行：

```
主题词                           机会分      需求     仓库数  注册表
agent-ide                       63.5  0.6833      28  空位
ocr-python                      33.9  0.5062     621  空位
data-collection                 28.1  0.4969    1873  空位
asyncio                          8.9  0.4969    7662  已有命中
ai-agents                        0.0  0.6833  120829  已有命中
```

三列一起读，少读一列就会误判：

- **机会分** —— 只是排序键，永远不是结论。
- **仓库数** —— 供给的绝对量。28 和 120829 是两个世界。
- **注册表** —— 「空位」= 技能注册表里没有语义命中。

注意最后一行：`ai-agents` 和 `agent-ide` **需求完全一样**（同一个热榜仓库触发），得分却是 0，
因为已经有 12 万个仓库挂着这个标签。这个落差就是整个产品。

## 两个信号，两种骗法

| 信号 | 怎么测 | 会怎么骗你 |
|---|---|---|
| **话题稀缺** | 热榜仓库的 topic，对应仓库总数 | 仓库少可能只是**没人用它打标签**，不代表没人做 |
| **注册表空位** | 拿 topic 查技能注册表，只有地板分（<0.055）说明无语义命中 | 空位可能意味着**没人想要**，而不是没人做 |

两者描述的都是供给。**都不证明需求。** 热榜衡量注意力，不衡量付费意愿，也不衡量留存。
报告每次都会把这句打出来。

## 快速开始

```bash
pip install build-next        # 或：pip install -e .
buildnext scan --limit 10 --max-topics 14 --md brief.md --site docs
```

| 参数 | 含义 |
|---|---|
| `--limit` | 每个分桶深挖几个 trending 仓库（默认 12） |
| `--max-topics` | topic 查询上限，受 GitHub 搜索 30 次/分 配额约束 |
| `--md` | 输出 agent 可读的简报到文件 |
| `--site` | 一次写出中英双语页面 |
| `--json` | 机器可读 |
| `--no-registry` | 跳过注册表探测 |

一次完整跑 1–3 分钟——它在做几十次实时 API 调用，限速是故意的。

## 推荐之前必须先验证

稀缺本身不是机会。先确认这个 topic 上已经站着谁：

```bash
gh api "search/repositories?q=topic:agent-ide&sort=stars&per_page=10" \
  --jq '.items[] | "\(.full_name) ★\(.stargazers_count) — \(.description)"'
```

前几名都是几百星的成熟项目 → **供给不薄，只是标签没铺开**。只有清一色 0–5 星、甚至几乎没结果，
才是真空位。`SKILL.md` 把这一步写成了硬性前置。

## 工具负责测量，agent 负责想象

CLI 刻意停在证据层。把「给谁做、为什么现在做、最小版本是什么」写出来是判断，不是计算——
所以 `SKILL.md` 把这一步交给 agent，并规定每条建议必须包含五件事：做给谁 / 解决什么 /
为什么是现在（引用真实数字）/ 最小可行版本 / 最大的风险。

规则引擎不擅长想象，这个工具也不假装擅长。

## 当作 agent skill 用

```bash
cp -r . ~/.workbuddy/skills/build-next
```

然后问它「我该做什么项目」，或者挂成每日定时任务当一块看板。

## 诚实的边界

- 热榜是**动量榜**，不是市场调研。一个方向可以又热又没钱赚。
- topic 是用户自己打的，极不规范。停用词表能滤掉生态标签，但噪声仍然存在。
- 分数**只在同一次运行内可比**。百分位来自本次候选集，跨天比分数没有意义——要比就比成员变化。

## 许可证

MIT。请重测，不要相信这个文件。
