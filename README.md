# Daily Info Radar · 每日信息雷达

一个可分享的 AI 研究 Skill 和离线新闻看板。将新闻、GitHub、Hacker News、Product Hunt、Reddit、地产组织成六层，每层约5条，并区分事实、厂商主张、个人经历和待核实项。地产层优先上海政策原文、市场、土地与融资。

重点是可追溯的信息，而不是凑足条数或热度排名。具备逐项证据评分、事件去重、昨日自然日窗口、历史归档、搜索、收藏和阅读状态。界面为自包含HTML，可直接离线打开。

## 安装

把 `skills/daily-info-radar` 整个文件夹复制到你的助手支持的Skill目录。例如当前Codex用户目录通常为 `~/.codex/skills/daily-info-radar`；其他客户端按其说明安装。

在支持Skill的助手中输入：

> 使用 $daily-info-radar，搜索昨天的 AI/科技、金融/商业与上海地产信息，保存到我的 daily-info-radar 文件夹。

需要能联网检索的AI助手及Python 3.10+。生成器仅使用Python标准库；其他IANA时区在Windows可能需自行安装tzdata，Asia/Shanghai内置回退无需额外包。Agent Reach、Firecrawl不是硬依赖。

## 两部分如何工作

1. AI助手根据Skill检索、追读、核验，写出符合 `references/data-schema.md` 的 reviewed.json。
2. 确定性生成器校验该JSON并生成日报、历史看板和离线ZIP：

```sh
python skills/daily-info-radar/scripts/window.py
python skills/daily-info-radar/scripts/build_dashboard.py --input reviewed.json --output-root ./radar-data
```

**这些Python脚本不执行新闻搜索、不调用模型。** 不能把生成器设置成定时任务后就期待它自己产生新闻。让支持定时执行的AI助手每日运行本Skill即可。

默认时间窗口是北京时间“昨天00:00至今天00:00”，不是最近24小时。GitHub等缺少历史快照时说明“抓取日发现”，不伪造昨日排行；信息不足则标记补充范围或缺口。

## 离线与历史

`radar-data/index.html` 是固定入口。`daily/YYYY-MM-DD/` 保留各期JSON、Markdown、HTML和候选/来源日志；`downloads/` 为离线包。相同版号不同内容会拒绝覆盖，更正须使用新版本号。用最新根入口浏览，可切换全部已保存日期。

断网可读已保存的正文、摘要、评分与证据说明；第三方原网页未整站下载，点原文需联网。收藏/已读存于该浏览器，本地文件与localhost可能不共享，换浏览器也不共享；不提供云同步。

## 定时运行

向支持定时任务的助手提出：“每天北京时间上午10点使用 $daily-info-radar 搜索昨日的信息，并保存到指定目录。”由该助手创建真实调度并核对状态。需要本机文件时，电脑与桌面应用应保持运行；此分享包不会自动创建任务或复制作者的账号配置。

参考任务提示词在 `automation-prompt.md`。可选偏好见 `radar.config.example.json`。

## 分享与GitHub

本目录是源代码仓库内容，可直接上传GitHub。不要上传个人日报、配置、浏览器资料或密钥。本项目默认没有任何作者凭据，也没有预设需要复用的账号。

参考 [Horizon](https://github.com/Thysrael/Horizon) 的聚合与去重思路；R是本项目设计的证据完整度，不是真实概率，也不是Horizon官方评分规则。UI曾按 [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines) 检查。

源代码按MIT许可；研究中引用的第三方文章和材料保留各自权利。
