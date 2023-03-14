# auto_comment
JD自动评价（带图评价晒单，追评，服务评价）

青龙拉库命令 ql repo https://github.com/6dylan6/auto_comment.git "jd_" "" "jdspider"

如果运行报依赖错误，运行评价依赖安装任务，没有问题不要运行

浏览器登录抓取CK（PC端CK），添加变量PC_COOKIE，每次运行评价10个订单

www的那个地址抓CK，登录后F12点到network，不要用命令document.cookie抓，会不完整，找带cookie的请求复制（其实只复制thor=xxx这串就行）

有问题欢迎提pr、issue

更新日志：
2022/11/6 新增多账号； 报错不停止运行；倒序评价，优先比较老的订单

2022/11/16 修复有些订单匹配不到pid；服务评价报错

2022/11/20 随机选取评价图片

2023/1/7 正常运行，有问题的多跑几次看看

2023/3/14 正常使用

![image](https://i.postimg.cc/NG6g4pHf/1.jpg)