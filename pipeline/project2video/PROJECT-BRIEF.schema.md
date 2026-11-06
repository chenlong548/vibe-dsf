# PROJECT-BRIEF.json 契约（项目介绍视频 · 事实源）

> 产出口径见 `PROMPT-PROJECT.md`。校验闸：`validate_brief_project.py`。
> 与 PAPER-BRIEF 的区别：features 带 proof（防吹牛）、quickstart 进画面（终端窗）、
> pain.old_way_cost 专门给 hook 对撞积木用。

```jsonc
{
  "meta": {
    "repo": "owner/name",              // GitHub 仓库全名
    "title": "展示名（可中文别称）",
    "one_liner": "≤32字一句话定位",     // 它是什么 + 给谁 + 核心价值
    "audience": "目标用户",
    "language": "主语言/技术栈",
    "duration_target": 50,             // 秒；项目片建议 40-70s，落 126BPM 拍网格
    "bpm": 126,
    "style": "paper"                   // 固定 paper（浅底项目风，独立站同源）
  },
  "pain": {
    "who": "谁有这个痛（口语）",
    "problem": "痛什么（口语，≤40字）",
    "old_way_cost": "旧做法的时间/成本，如 '3 天'、'500 行配置'——给 hook 对撞用"
  },
  "hook_candidates": [
    { "claim": "≤32字反差钩子", "why_it_works": "为什么抓人（一句话）" }
  ],
  "features": [
    {
      "name": "特性名 ≤8字",
      "what": "人话一句话 ≤32字",
      "proof": "证据：README 数字/命令/真实输出/文件路径（必填，不许空话）"
    }
  ],
  "quickstart": {
    "install": ["命令1", "命令2"],      // 1-3 条，按 README 原文
    "first_output": "首次运行的真实输出摘录（终端窗素材）",
    "time_to_demo": "从零到跑起来要多久（口语，如 '一分钟'）"
  },
  "metrics": [
    {
      "value": "数字（如 9.5）",
      "unit": "单位（如 /10、%、万）",
      "claim": "这句话想说什么",
      "comparison": "和什么比（没有对比写 '绝对值'）",
      "source": "README/repo 具体位置；stars 标统计时间"
    }
  ],
  "limits": ["项目边界 ≥1 条：不支持什么/只验证过什么（防吹牛）"],
  "cta": {
    "repo_url": "https://github.com/owner/name",
    "install_short": "一行安装/克隆命令"
  }
}
```
