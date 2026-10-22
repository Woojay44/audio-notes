# audio-notes

把上课录音在本地转写成带时间戳的文字稿，再由 [Claude Code](https://claude.com/claude-code) 按知识主题整理成**教材式、带复习题**的 Obsidian 笔记。转写免费，录音不离开你的电脑。

```
录音（m4a/mp3/wav…） ──► faster-whisper 本地转写（GPU） ──► transcripts/*.txt
                                                              │
                         Claude Code（audio-notes skill） ◄───┘
                                     │
                                     ▼
            Obsidian：<学期>/<课程>/<课程>-第N周-<主题>.md
            （概览 · 知识框架图 · 定义 / 考点框 · 对比表 · 流程图 · 考点速记 · 折叠复习题）
```

## 特点

- **本地免费转写**：faster-whisper `large-v3-turbo` + GPU，45 分钟的课约 1–4 分钟转完；没有 GPU 时自动改用 CPU。
- **针对课堂录音调过**：
  - 关闭“以上文为提示”，避免 Whisper 在长录音里陷入重复或幻觉循环；
  - 过滤常见的幻觉套话（“请不吝点赞订阅……”）；
  - 繁体转简体，去掉混入的日文假名和韩文；
  - 按停顿把碎句合并成段落，每段带时间戳；
  - `--terms` 传入课程术语，减少同音错字。
- **笔记按主题组织**，不按录音分：同一主题跨多段录音会合成一份，下周接着讲会并进已有的笔记。
- **个人配置与代码分离**：库路径、课程表等写在不入库的 `skill/local.md` 里。

## 环境要求

- Windows + WSL2（Ubuntu），NVIDIA 显卡（可选）
- [Claude Code](https://claude.com/claude-code)
- [Obsidian](https://obsidian.md/)（笔记用了 callout 和 mermaid）

> 为什么跑在 WSL 里：开启 Windows「智能应用控制」的电脑会拦截 `ctranslate2`、`av` 等未签名 DLL，导致 Windows 版 faster-whisper 无法加载；WSL 不受影响，也能直接使用 GPU。没有这个限制的话，脚本稍作修改也可以在 Windows 或 Linux 上原生运行。

## 安装

**1. 在 WSL 里装转写环境**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # 已有 uv 可跳过
uv venv -p 3.12 ~/.venvs/audio-notes
VIRTUAL_ENV=~/.venvs/audio-notes uv pip install -r requirements-wsl.txt
```

第一次转写时会自动下载 `large-v3-turbo` 模型（约 1.6GB）。

**2. 把 skill 装进 Claude Code**（Windows PowerShell，在项目目录下执行）

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\audio-notes" -Target "$PWD\skill"
Copy-Item skill\local.example.md skill\local.md   # 然后填上你的路径和课程表
```

## 使用

**一条龙**：把录音放进项目根目录，在 Claude Code 里说“有新录音，计算机网络第三周”。Claude 会依次：

1. 转写；
2. 通读文字稿，按主题写笔记并配复习题；
3. 把笔记放进 Obsidian 对应的课程目录；
4. 把录音移到 `audio/` 归档。

**只转写**：

```bash
# WSL 里
bash transcribe.sh '/mnt/d/录音/第三周.m4a' --terms '计算机网络,TCP,拥塞控制'
# Windows 里（路径可以写成 Windows 形式，会自动转换）
wsl -e bash /mnt/d/path/to/audio-notes/transcribe.sh 'D:\录音\第三周.m4a'
```

在 Git Bash 里调用 `wsl` 时，命令前要加 `MSYS_NO_PATHCONV=1`。

| 参数 | 作用 |
|---|---|
| `--terms "术语1,术语2"` | 课程术语，提高专业词识别率 |
| `--model medium` | 换更小的模型（更快，准确率略低） |
| `--out <目录>` | 输出目录，默认 `transcripts/` |
| `--force` | 已转写过的也重新转 |

## 目录

```
transcribe.py            转写脚本
transcribe.sh            WSL 启动脚本（设置 CUDA 库路径）
requirements-wsl.txt     WSL 环境依赖
skill/SKILL.md           Claude Code skill：转写 → 读稿 → 按主题写笔记 → 放进 Obsidian
skill/local.example.md   本机配置示例（复制为 local.md，不入库）
transcripts/  audio/     转写稿、已处理的录音（不入库）
```

## 已知局限

- 教室远场录音的专业术语错字较多。笔记阶段由 Claude 根据上下文纠正，实在确定不了的会列进“待核对”。录音时手机离讲台越近越好。
- 转写不区分说话人。
- 实测对比过：`large-v3` 比 `large-v3-turbo` 慢约 3 倍，而且更容易产生幻觉；FunASR Paraformer 在这类录音上断句较乱。所以默认用 turbo。

## License

MIT
