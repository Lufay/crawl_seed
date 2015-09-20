# crawl_seed
crawl seed by BeautifulSoup4

ver1
1. 帖子列表逆序遍历
2. 启动前载入上次已下载的文件，做字典{url: localdir}
3. 一旦重图，则后续图都不再下载

ver2
1. 解决跨页的连贯性问题
2. 帖子标题匹配失败记录，便于分析是真的无用，还是正则缺陷
3. urlopen全部加入异常控制的重试
4. 解决&#[^\d]网页截断的问题，升级html5lib解析器，解决form不作为table的parent元素的问题
5. 对跳转到xunfs的下载链接进行失败重试，直到跳转到rmdown
6. 函数进行拆分，便于import进行模块调用

ver3
1. 重试递增延时
2. 下载种子失败汇报
3. 规范化参数（支持版本、路径、cache、mosaic指定）
4. 修改一些返回值判定不完全的地方（有可能漏报）

ver3.1
1. 完善page_pattern
2. 对open_page返回None的检查

ver3.2(trunk)
1.重构load_log为类HasDownloadLog，强化复用
2.修改download函数的返回值为(bool, "info"), 和crawl_subject相一致
3.增加GetFileLine的类（为checklog.py服务，后者可以合并到trunk）
4.download函数增加内容检查机制
5.增加not_refresh的内容检查函数，如果是Refresh，则重试15次（貌似那么好用）
6.兼容mosaic和occident页面抓取
