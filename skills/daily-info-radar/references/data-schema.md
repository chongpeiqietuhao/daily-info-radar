# reviewed.json

UTF-8 JSON。结构校验不能代替事实核验。数字/日期/专名需能追溯同条source_ids或claim.source_ids。不要存密钥。

顶层字段：

- schema_version=`2.0`，edition为唯一安全版号（`2026-09-23-full`，更正`2026-09-23-r2`）；report_date为目标日期YYYY-MM-DD。
- timezone默认Asia/Shanghai；completed_at/cutoff_at为实际完成/截止ISO时间含偏移。
- window_start/window_end为目标自然日边界；旧版导入可以省略。
- research_window、run_mode为可读窗口/扩展说明及手动/定时模式。
- sources、items为下述数组；top最多3项{id,reason}，id引用items。
- candidates为{title,url,layer,discovered_at,full_text_read,decision,reason}数组；旧版无日志时空数组并在limitations说明。
- research_log、limitations为字符串数组；horizon_note说明方法参考与差异。
- rubric可选；counts由生成器重算，不信任传入计数。

来源字段：id,name,url,layer,status,note,method,retrieved_during,upstream_fetch_time。url为http/https或null（本机错误）；状态为成功/部分成功/无法获取/失败/未尝试。未知时间不虚构。

条目字段：id,event_id,layer,title,summary,value,angle,unknown,source_ids,topic,published_at,event_time,updated_at,freshness,verified_at,claims。

layer为1—5；topic为AI/科技或金融/商业；unknown字符串数组。时间缺失用null。freshness精确写昨日/近三日补充/抓取日发现。detail可选对象，GitHub/PH应有用途、门槛、许可/价格、维护、试用状态。

claims非空，每项text,kind,R,components,source_ids,boundary。R为四项之和，无证据R和components均null。例如：

```json
{"text":"明确限定的主张","kind":"当事方主张","R":55,"components":{"原始性":30,"支持程度":15,"独立复核":0,"时间与口径":10},"source_ids":["source-id"],"boundary":"仅当事方自述，实际效果未测。"}
```

同主题跨日有实质更新时使用新条目id，event_id可沿用，避免误继承已读状态。更正用新edition并描述更正，不覆盖旧记录。
