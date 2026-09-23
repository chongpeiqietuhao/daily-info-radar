# 来源策略

入口用于发现线索，不是永久可信名单。用户可以替换为自己的主题和地区来源。

| 层 | 发现入口 | 入选后追读 |
|---|---|---|
| 新闻 | 公司/实验室新闻页、公开RSS、央行/监管、公司IR | 官方公告、技术报告、模型卡、统计表、原始财报 |
| GitHub | https://github.com/trending 、Releases/Commits | README、许可证、真实变更，未知维护频率明确标注 |
| HN | https://news.ycombinator.com/ 及公开历史搜索 | item?id=永久链接、原文和具体评论 |
| PH | https://www.producthunt.com/ 及公开往期榜单 | 活动页、官网、定价/平台限制；“今天”不自动等于目标自然日 |
| Reddit | LocalLLaMA、ClaudeCode、selfhosted等相关社区 | comments/永久原帖、配置/任务/失败过程；保留样本偏差 |

新闻例：MiMo、Anthropic、OpenAI、GitHub Blog、IBM Newsroom。金融例：人民银行、国家统计局、交易所、公司IR。不要求每天这些机构都有新闻。

获取失败依次尝试已有授权工具、公开网页/RSS/API、公开搜索/可靠聚合。少量不同路线仍失败则记录可观察原因；避免反复撞同一失败入口。导航、缓存目录、Removed不是正文。

没有昨日GitHub榜单快照时可用抓取日榜单作为发现补充，明确标记，不能恢复昨日排行。优先保存实际榜单观察时点；后续才能可靠回看。
