你可以在 `git log` 命令中添加 `--date` 和 `--pretty` 参数来显示提交时间。以下是推荐的命令，**在保留 `--all --oneline --graph --decorate` 的基础上增加时间显示**：

```bash
git log --all --graph --decorate --pretty=format:"%h %ad %d %s" --date=short
```

### 各部分说明：
- `%h`：简短的 commit hash（如 `a1b2c3d`）
- `%ad`：作者日期（author date），格式由 `--date=` 控制
- `%d`：引用信息（如分支名、tag，即 `decorate` 内容）
- `%s`：提交信息（subject）
- `--date=short`：日期格式为 `YYYY-MM-DD`（你也可以用 `iso`、`relative` 等）

---

### 其他常用时间格式选项：
| 选项 | 示例 |
|------|------|
| `--date=short` | `2025-10-28` |
| `--date=iso` | `2025-10-28 14:30:00 +0800` |
| `--date=relative` | `2 hours ago` |
| `--date=local` | 使用本地时区 |

---

### 如果你仍希望“一行显示”但带时间，可以这样：
```bash
git log --all --graph --decorate --oneline --date=short --pretty=format:"%h %ad %d %s"
```

> ?? 注意：`--oneline` 实际上是 `--pretty=oneline` 的简写，会覆盖自定义 `--pretty=format:...`，所以**不能同时用 `--oneline` 和 `--pretty=format`**。上面命令中保留了 `--oneline` 仅作示意，实际应**去掉 `--oneline`**，否则时间不会显示。

---

### ? 最终推荐命令（带时间、图形、所有分支、简洁）：
```bash
git log --all --graph --decorate --pretty=format:"%C(auto)%h %C(green)%ad %C(reset)%d %s" --date=short
```

这个版本还加了颜色（`%C(auto)` 自动着色），视觉更清晰。

要在 Git 中**临时保存当前工作、切换到另一个分支进行开发（或修复）、再合并回来**，推荐使用以下标准流程：

---

### ? 场景说明
- 你在 `main` 或某个功能分支上工作，但工作**还没完成**
- 现在需要**临时切到另一个分支**（比如 `hotfix` 或 `dev`）做修改
- 完成后要**把修改合并回原分支**

---

## ?? 正确操作步骤

### 1. **保存当前未完成的工作（可选）**
如果你有未提交的更改，但又不想现在 commit，可以用 `stash`：

```bash
git stash push -m "临时保存 feature 工作"
```

###> 这会把当前工作区和暂存区的改动“藏起来”，工作区变干净。***

---

### 2. **切换到目标分支**
```bash
git checkout target-branch      # 例如 git checkout dev
# 或用新语法
git switch target-branch
```

> 如果目标分支不存在，可以用：
> ```bash
> git switch -c new-hotfix-branch
> ```

---

### 3. **在目标分支上开发并提交**
```bash
# 修改文件...
git add .
git commit -m "修复某个问题"
```

---

### 4. **切换回原来的分支**
```bash
git switch original-branch      # 例如 git switch main 或你的功能分支
```

---

### 5. **恢复之前的工作（如果有 stash）**
```bash
git stash pop   # 恢复最近一次 stash 并删除它
# 或
git stash apply # 恢复但保留 stash（用于多次复用）
```

> 如果有冲突，手动解决即可。

---

### 6. **合并目标分支的修改**
```bash
git merge target-branch
```

例如：
```bash
git merge hotfix-login-bug
```

> 这会把 `target-branch` 的 commit 合并到当前分支。

---

## ?? 示例流程（完整）

```bash
# 当前在 feature-a，工作未完成
git stash push -m "WIP on feature A"

# 切到 main 修复紧急 bug
git switch main
# 修改代码...
git add .
git commit -m "Fix critical bug in auth"

# 切回 feature-a
git switch feature-a

# 恢复之前的工作
git stash pop

# 把 main 的修复合并进来（可选，但推荐）
git merge main
```

---

## ?? 补充建议

- 如果你只是想**临时测试或查看其他分支**，不需要 `stash`，直接 `git switch` 即可（前提是工作区干净）。
- 如果你已经做了 commit，就**不需要 stash**，直接切换分支即可。
- 合并前建议先 `git pull` 确保分支最新。

---

需要我根据你的具体分支名（比如 `main`、`dev`、`feature/xxx`）生成定制命令吗？

你想把**原来在某个分支上修改但尚未提交（或已 stash）的文件**，**应用到新切换的分支（比如 `feature/integrated-voice-recognition`）中**，这是 Git 中非常常见的场景。以下是清晰、安全的操作步骤：

---

### ? 场景回顾
- 你在某个分支（比如 `main` 或 detached HEAD）上做了修改
- 你执行了 `git stash` 保存了这些修改（从你的日志看，已经做了）
- 然后你尝试切换到远程分支，但失败了（因为不能直接 `switch` 到 `origin/xxx`）
- 现在你想：**在正确的本地功能分支上恢复这些修改**

---

### ? 正确操作流程

#### 1. **创建并切换到本地功能分支**
```bash
git switch -c feature/integrated-voice-recognition --track origin/feature/integrated-voice-recognition
```
> 这会基于远程分支创建同名本地分支，并自动设置跟踪。

#### 2. **恢复你之前 stash 的修改**
```bash
git stash pop
```
> 这会把最近一次 stash 的内容恢复到工作区，并从 stash 列表中删除。

如果你不确定 stash 列表内容，可以先查看：
```bash
git stash list
```
输出类似：
```
stash@{0}: On (no branch): 临时保存 feature 工作
```

---

### ? 如果你还没 stash（但有未提交修改）
如果你**还没 stash**，但工作区有修改，也可以直接切换分支（前提是 Git 认为不会冲突）：
```bash
git switch feature/integrated-voice-recognition
```
Git 会自动携带未提交的更改到新分支（只要文件不冲突）。

> ?? 但如果 Git 拒绝切换（提示“would be overwritten”），那就必须先 `stash`。

---

### ? 验证结果
- 运行 `git status`，确认你的修改已出现在新分支
- 运行 `git branch`，确认当前在 `feature/integrated-voice-recognition`
- 然后你可以 `git add` + `git commit` 提交这些修改

---

### ?? 总结命令（你当前最可能需要的）
```bash
# 1. 创建并切换到本地功能分支
git switch -c feature/integrated-voice-recognition --track origin/feature/integrated-voice-recognition

# 2. 恢复之前 stash 的修改
git stash pop
```

完成后，你原来修改的文件就“放进”了新分支，可以继续开发或提交。

需要我帮你检查当前状态（比如 `git status` 输出）吗？